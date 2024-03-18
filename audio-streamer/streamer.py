import asyncio
import websockets
import pyaudio
import os
import threading

# 音声データのフォーマット設定
WS_AUDIO_INPUT_URL = os.getenv("WS_AUDIO_INPUT_URL", "")
FORMAT = pyaudio.paInt16  # 16ビットフォーマット
BUFFER_DURATION_SECOND = 3
BUFFERING_INTERVAL_SECOND = 0.5 # Bufferデータを更新する間隔
CHANNELS = 1  #
RATE = 44100  # サンプルレート
CHUNK = 10240  # データのチャンクサイズ

buffer = bytes()


def read_audio(stream, stop_event):
    global buffer
    while not stop_event.is_set():
        data = stream.read(CHUNK, exception_on_overflow=False)
        buffer += data


async def send_audio(uri, stop_event):
    global buffer
    while not stop_event.is_set():
        try:
            async with websockets.connect(uri) as websocket:
                print("マイク入力を開始します")
                while not stop_event.is_set():
                    if len(buffer) >= RATE * CHANNELS * 2 * BUFFER_DURATION_SECOND:  # 2秒分のデータ
                        await websocket.send(buffer)
                        buffer = bytes()
                    else:
                        await asyncio.sleep(BUFFERING_INTERVAL_SECOND)
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"WebSocket接続が閉じられました: {e}")


def main():
    stop_event = threading.Event()
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    read_thread = threading.Thread(target=read_audio, args=(stream, stop_event))
    read_thread.start()

    try:
        asyncio.run(send_audio(WS_AUDIO_INPUT_URL, stop_event))
    finally:
        stop_event.set()
        read_thread.join()
        stream.stop_stream()
        stream.close()
        audio.terminate()


if __name__ == "__main__":
    main()
