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

HOST = "localhost"
PORT = 8765

# TO_LANGUAGE = "English"
TO_LANGUAGE = "Japanese"
FROM_LANGUAGES_SUPPORTED = ["English", "Japanese"]

NOISY_PATTERNS_REGEXP = [
    "The provided text seems to be missing.",
    "Please provide a full sentence",
    "Please provide a complete sentence",
    "Please provide a sentence",
    r"^.$",
    r"^ .$",
    r"【.*】",
    r"^Dumb?.$",
    r"(?i)thank?s?.*for watching",
    r"(?i)If you liked this video.*please subscribe.*like button",
    r'""',
    "Silence.",
    "Peace.",
    "Bye.",
    "Thank you.",
    "PewDiePie",
    "視聴.*ありがとう",
    "ご覧.*ありがとう",
    "はじめしゃちょー",
]

# Audio
AUDIO_FILE_FORMAT = "flac"
AUDIO_SAMPLE_WIDTH = 2  # 16bit
AUDIO_FRAME_RATE = 44100  # 44100Hz
AUDIO_CHANNELS = 1  # monaural

# Translation
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
            language, segments = await atranscribe_streaming_simple(tmpfile_path)

            from_language = language.name
            to_language = TO_LANGUAGE

            if from_language not in FROM_LANGUAGES_SUPPORTED:
                continue

            async for segment in segments:
                transcribed_text = segment["text"]
                print(f"[DEBUG] transcribed: [{from_language}] {transcribed_text}")

                translated_text = translate(
                    client, transcribed_text, from_language, to_language
                )
                if translated_text == "":
                    continue
                elif translated_text != transcribed_text:
                    print(f"[DEBUG] translated: [{to_language}] {translated_text}")

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
        audio_segment = AudioSegment(
            data=audio_bytes,
            sample_width=AUDIO_SAMPLE_WIDTH,
            frame_rate=AUDIO_FRAME_RATE,
            channels=AUDIO_CHANNELS,
        )
        audio_segment.export(tmpfile, format=format)
        return tmpfile.name


def is_noisy_text(text, noisy_patterns):
    return any(re.search(pattern, text) for pattern in noisy_patterns)


def translate(client, text, from_language, to_language):
    if is_noisy_text(text, NOISY_PATTERNS_REGEXP):
        return ""

    if from_language == to_language:
        return text
    else:
        return translate_text(client, text, from_language, to_language)


def translate_text(client, text, from_language, to_language):
    response = client.chat.completions.create(
        model=TRANSLATION_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    f"You will be provided with a sentence in {from_language}."
                    + f"Your task is to translate it into {to_language}."
                    + "If the sentence is incomplete, choose an empty string."
                    + "The sentence provided is for an online meeting, so please make it as natural conversational text as possible"
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
