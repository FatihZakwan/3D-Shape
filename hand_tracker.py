"""
hand_tracker.py
================
Backend Python untuk "3D Shape Sandbox" berbasis gesture tangan.

Tugas file ini:
1. Membuka webcam.
2. Mendeteksi tangan (sampai 2 tangan) pakai MediaPipe Hands.
3. Menghitung gesture "pinch" (jempol + telunjuk ketemu).
4. Mengirim gambar webcam + data landmark tangan ke browser lewat WebSocket,
   supaya bisa dirender jadi AR overlay pakai Three.js di index.html.

Cara pakai:
    pip install -r requirements.txt
    python hand_tracker.py

Lalu buka index.html di browser (boleh langsung double-click filenya).
"""

import asyncio
import base64
import json
import math
import time

import cv2
import mediapipe as mp
import websockets

# ----------------------------------------------------------------------
# Konfigurasi
# ----------------------------------------------------------------------
CAM_INDEX = 0          # ganti kalau webcam-mu bukan device pertama
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
JPEG_QUALITY = 60      # lebih kecil = lebih ringan tapi kurang tajam
TARGET_FPS = 24

WS_HOST = "localhost"
WS_PORT = 8666

# Ambang batas pinch (rasio jarak jempol-telunjuk terhadap ukuran tangan).
# Dibuat dua ambang (hysteresis) biar status pinch tidak "kedip-kedip".
PINCH_ENTER_RATIO = 0.35   # di bawah ini -> dianggap MULAI pinch
PINCH_EXIT_RATIO = 0.55    # di atas ini -> dianggap LEPAS pinch

SMOOTHING = 0.55   # exponential smoothing untuk landmark (0=diam, 1=tanpa smoothing sama sekali)

mp_hands = mp.solutions.hands


class HandSmoother:
    """Smoothing sederhana (EMA) supaya titik landmark tidak jitter/gemetar."""

    def __init__(self):
        self.prev = None

    def smooth(self, landmarks):
        if self.prev is None or len(self.prev) != len(landmarks):
            self.prev = landmarks
            return landmarks
        out = []
        for (px, py, pz), (x, y, z) in zip(self.prev, landmarks):
            nx = px + (x - px) * SMOOTHING
            ny = py + (y - py) * SMOOTHING
            nz = pz + (z - pz) * SMOOTHING
            out.append((nx, ny, nz))
        self.prev = out
        return out


def dist2d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class HandTrackerServer:
    def __init__(self):
        self.clients = set()
        self.smoothers = {}      # key: label tangan ("Left"/"Right") -> HandSmoother
        self.pinch_state = {}    # key: label tangan -> bool

    # -------------------- WebSocket plumbing --------------------
    async def register(self, websocket):
        self.clients.add(websocket)
        print(f"[+] Client terhubung ({len(self.clients)} total)")
        try:
            await websocket.wait_closed()
        finally:
            self.clients.discard(websocket)
            print(f"[-] Client terputus ({len(self.clients)} total)")

    async def broadcast(self, message):
        if not self.clients:
            return
        stale = []
        for ws in list(self.clients):
            try:
                await ws.send(message)
            except websockets.exceptions.ConnectionClosed:
                stale.append(ws)
        for ws in stale:
            self.clients.discard(ws)

    # -------------------- Capture + deteksi tangan --------------------
    async def capture_loop(self):
        cap = cv2.VideoCapture(CAM_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

        if not cap.isOpened():
            raise RuntimeError(
                "Tidak bisa membuka webcam. Cek CAM_INDEX, atau pastikan tidak "
                "dipakai aplikasi lain, atau izin kamera sudah diberikan."
            )

        frame_interval = 1.0 / TARGET_FPS

        with mp_hands.Hands(
            model_complexity=0,
            max_num_hands=2,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5,
        ) as hands:
            print("Kamera siap. Mulai deteksi tangan...")
            while True:
                loop_start = time.time()
                ok, frame = cap.read()
                if not ok:
                    await asyncio.sleep(0.05)
                    continue

                # Mirror frame supaya terasa seperti cermin (natural buat interaksi)
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb)

                hands_payload = []
                seen_labels = set()

                if results.multi_hand_landmarks and results.multi_handedness:
                    for hand_landmarks, handedness in zip(
                        results.multi_hand_landmarks, results.multi_handedness
                    ):
                        label = handedness.classification[0].label  # "Left" / "Right"
                        if label in seen_labels:
                            label = label + "_2"
                        seen_labels.add(label)

                        raw = [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]
                        smoother = self.smoothers.setdefault(label, HandSmoother())
                        smoothed = smoother.smooth(raw)

                        wrist = smoothed[0]
                        mcp_middle = smoothed[9]
                        thumb_tip = smoothed[4]
                        index_tip = smoothed[8]

                        hand_size = max(dist2d(wrist, mcp_middle), 1e-4)
                        pinch_ratio = dist2d(thumb_tip, index_tip) / hand_size

                        was_pinching = self.pinch_state.get(label, False)
                        threshold = PINCH_EXIT_RATIO if was_pinching else PINCH_ENTER_RATIO
                        is_pinching = pinch_ratio < threshold
                        self.pinch_state[label] = is_pinching

                        pinch_point = (
                            (thumb_tip[0] + index_tip[0]) / 2.0,
                            (thumb_tip[1] + index_tip[1]) / 2.0,
                        )

                        hands_payload.append({
                            "id": label,
                            "landmarks": smoothed,       # 21 titik [x,y,z] (0..1, sudah mirrored)
                            "pinch": is_pinching,
                            "pinchRatio": round(pinch_ratio, 4),
                            "pinchPoint": pinch_point,
                        })

                # Bersihkan state tangan yang sudah tidak terlihat lagi
                for label in list(self.pinch_state.keys()):
                    if label not in seen_labels:
                        self.pinch_state.pop(label, None)
                        self.smoothers.pop(label, None)

                ok, buf = cv2.imencode(
                    ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
                )
                b64 = base64.b64encode(buf).decode("ascii") if ok else ""

                message = json.dumps({
                    "type": "frame",
                    "image": b64,
                    "hands": hands_payload,
                    "ts": loop_start,
                })
                await self.broadcast(message)

                elapsed = time.time() - loop_start
                await asyncio.sleep(max(0.0, frame_interval - elapsed))

    async def run(self):
        async with websockets.serve(
            self.register, WS_HOST, WS_PORT, max_size=2 ** 22
        ):
            print(f"WebSocket server jalan di ws://{WS_HOST}:{WS_PORT}")
            print("Sekarang buka index.html di browser (double-click juga bisa).")
            await self.capture_loop()


def main():
    server = HandTrackerServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\nDihentikan oleh user. Sampai jumpa!")


if __name__ == "__main__":
    main()