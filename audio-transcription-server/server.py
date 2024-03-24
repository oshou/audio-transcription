import asyncio
import os
import re
import tempfile
import websockets
from websockets.exceptions import ConnectionClosed
from pydub import AudioSegment
from whisperstream import atranscribe_streaming_simple
from whisperstream.error import UnsupportedLanguageError
from openai import OpenAI

FROM_LANGUAGES_SUPPORTED = ["Japanese", "English"]
TO_LANGUAGE = "Japanese"
NOISY_MESSAGES_REGEXP = [
    r"^\.$",
    r"Thanks? you for watching",
    "Your input seems incomplete. Please provide a full sentence for translation.",
    "The provided text seems to be missing. Could you please provide a valid sentence?",
    "Thank you so much for watching, and I'll see you in the next video.",
    "視聴していただきありがとうございます",
    "ご視聴ありがとうございました",
    "ご覧いただきありがとうございます",
]
AUDIO_FILE_FORMAT = "flac"
TRANSLATION_MODEL = "gpt-4"
TRANSLATION_MAX_TOKENS = 64
TRANSLATION_TEMPERATURE = 0.7
TRANSLATION_TOP_P = 1

shared_state = {"translated": []}
event = asyncio.Event()


async def audio_input_handler(websocket):
    print("WebSocket connected")

    client = OpenAI()

    while True:
        audio_bytes = await websocket.recv()

        tmpfile_path = create_temporary_audio_file(audio_bytes, AUDIO_FILE_FORMAT)

        try:
            language, segments = await atranscribe_streaming_simple(tmpfile_path, file_format)
            from_language = language.name

            if from_language not in FROM_LANGUAGES_SUPPORTED:
                continue

            async for segment in segments:
                transcribed_text = segment["text"]

                if is_noisy_message(transcribed_text):
                    continue

                if from_language != TO_LANGUAGE:
                    translated_text = translate_text(client, transcribed_text, from_language, TO_LANGUAGE)
                else:
                    translated_text = transcribed_text

                shared_state["translated"].append(translated_text)
                event.set()

            os.remove(tmpfile_path)
        except UnsupportedLanguageError as e:
            print(f"Unsupported Language: {e}")
        except ConnectionClosed as e:
            print(f"WebSocket disconnected: ${e}")
        except Exception as e:
            print(f"Internal server error: {e}")


async def text_output_handler(websocket):
    try:
        while True:
            await event.wait()

            for text in shared_state["translated"]:
                await websocket.send(text)

            shared_state["translated"].clear()
            event.clear()
    except ConnectionClosed as e:
        print(f"WebSocket disconnected: ${e}")


def create_temporary_audio_file(audio_bytes, format):
    with tempfile.NamedTemporaryFile(delete=False, suffix=format, mode="wb") as tmpfile:
        audio_segment = AudioSegment(data=audio_bytes, sample_width=2, frame_rate=44100, channels=1)
        audio_segment.export(tmpfile, format=format)
        return tmpfile.name


def is_noisy_message(text):
    return any(re.search(pattern, text) for pattern in NOISY_MESSAGES_REGEXP)


def translate_text(client, text, from_language, to_language):
    response = client.chat.completions.create(
        model=TRANSLATION_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    f"You will be provided with a sentence in {from_language}"
                    f"and your task is to translate it into {to_language}."
                    "If the sentence is incomplete, choose an empty string."
                ),
            },
            {"role": "user", "content": text},
        ],
        temperature=TRANSLATION_TEMPERATURE,
        max_tokens=TRANSLATION_MAX_TOKENS,
        top_p=TRANSLATION_TOP_P,
    )
    return response.choices[0].message.content


async def main():
    await websockets.serve(audio_input_handler, "localhost", 8765)
    await websockets.serve(text_output_handler, "localhost", 8766)
    await asyncio.Event().wait()


asyncio.run(main())
