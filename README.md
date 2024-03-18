# Audio Transcription

## Get started

### prerequisite

```
$ brew install direnv
$ brew install poetry
$ brew install ffmpeg
$ brew install portaudio
```

### audio-transcription-server

```
$ cd audio-transcription-server
$ cp -rp .env.local .env
# Edit .env (e.g. OPENAI_API_KEY)
$ direnv allow
$ poetry install --no-root
$ poetry update pydub
$ poetry run python server.py
```

### ui

```
$ cd ui
$ cp -rp .env.local .env
$ direnv allow
$ npm ci
$ npm start
```

### audio-streamer

```
$ cd audio-streamer
$ cp -rp .env.local .env
$ direnv allow
$ poetry install --no-root
$ poetry run python streamer.py
```

## Sequence

```mermaid
sequenceDiagram
  participant ASClient as AudioStreamer
  participant AT as AudioTranscription
  participant UI as UI
  participant OpenAI-API as OpenAI-API

  ASClient->>ASClient: マイクから音声キャプチャ
  ASClient->>AT: 音声データ(byte)<br/>を配信
  AT->>AT: 音声データ(byte)を音声ファイル(.ogg)に変換
  AT->>OpenAI-API: 音声ファイル(.ogg)の<br/>テキスト化<br/>
  OpenAI-API-->>AT:　
  AT->>UI: 翻訳テキストデータの配信
  UI->>UI: UIリアルタイム更新
```
