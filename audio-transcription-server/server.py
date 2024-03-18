import asyncio
import os
import tempfile
import websockets
from pydub import AudioSegment
import io
from whisperstream import atranscribe_streaming_simple

shared_state = {"output": []}
event = asyncio.Event()


async def audio_input_handler(websocket):
    async for audio_bytes in websocket:
        print("WS_AUDIO_INPUT_URL called")

        # conversion (bytes => audio-data(.ogg)
        buffer = io.BytesIO()
        audio_segment = AudioSegment(data=audio_bytes, sample_width=2, frame_rate=44100, channels=1)
        audio_segment.export(buffer, format="ogg")
        buffer.seek(0)  # バッファの先頭に戻る
        with tempfile.NamedTemporaryFile(delete=False, mode="wb", suffix=".ogg") as tmpfile:
            tmpfile.write(buffer.read())
            tmpfile_path = tmpfile.name

        # transcribe
        try:
            language, gen = await atranscribe_streaming_simple(tmpfile_path)
            async for segment in gen:
                print("文字起こしテキスト:", segment.text)
                shared_state["output"].append(segment.text)
                event.set()  # 処理が完了したらイベントを通知
            os.remove(tmpfile_path)
        except Exception as e:
            print(f"サポートされていない言語が検出されました: {e}")


async def text_output_handler(websocket):
    try:
        while True:
            # event wait start
            await event.wait()

            # output text to ws-client
            for text in shared_state["output"]:
                await websocket.send(text)  # 処理結果を送信
            shared_state["output"].clear()  # 送信後は結果をクリア

            # event reset
            event.clear()
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed with error: {e}")


async def main():
    await websockets.serve(audio_input_handler, "localhost", 8765)
    await websockets.serve(text_output_handler, "localhost", 8766)
    await asyncio.Event().wait()


asyncio.run(main())
