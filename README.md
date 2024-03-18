# Audio Transcription

## Prerequisite

```
$ brew install direnv
$ brew install ffmpeg
$ brew install portaudio
```

## Get started

### audio-transcription-server

```
$ cd audio-transcription-server
$ cp -rp .env.local .env
$ direnv allow
$ poetry run python server.py
```

### ui

```
$ cd ui
$ cp -rp .env.local .env
$ direnv allow
$ npm install
$ npm start
```

### audio-streamer

```
$ cd audio-streamer
$ cp -rp .env.local .env
$ direnv allow
$ npm install
$ poetry run python streamer.py
```
