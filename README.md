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

### AsIs

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

### ToBe

```mermaid
sequenceDiagram
  participant User
  participant ChromeExt as ChromeExtension
  participant AT as AudioTranscription<br/>Server
  participant OpenAI-API as OpenAI-API
  participant Store as Store
  participant GDocs-API as GDocs-API

  User->>ChromeExt: Meetページを開く
  ChromeExt->>AT: 表示中のMeetURLが音声入力中か確認
  AT->>AT: 音声受付中か確認<br/> ??どうやって??
  AT-->>ChromeExt: 　
  ChromeExt->>ChromeExt: StartRecording/Joinボタンを表示<br/>(言語は出来たら出し分け)
  User->>ChromeExt: StartRecording/Joinボタン押下
  ChromeExt->>AT: Websocketサーバへ接続
  AT-->>ChromeExt: 　
  loop While-Streaming
    ChromeExt->>AT: (音声入力者のみ)音声データ送信<br/>??どのサイズ+頻度で送るか??
    AT->>AT: 音声データ(byte)を<br/>一時音声ファイル(.ogg)に変換
    AT->>OpenAI-API: 一時音声ファイル(.ogg)の文字起こし<br/>??翻訳+文字起こしはまとめられないか??
    OpenAI-API-->>AT: 　
    AT->>OpenAI-API: 文字起こしテキストの翻訳<br/>
    OpenAI-API-->>AT: 　
    AT->>ChromeExt: 翻訳テキストデータの配信
    ChromeExt->>ChromeExt: UIリアルタイム更新
    AT->>Store: 翻訳テキストデータの追加保存<br/>MeetURL毎に保存は区別する
    AT->>AT: 一時音声ファイルを削除
  end
  User->>ChromeExt: Meet終了ボタンを押下(?)
  ChromeExt->>AT: Meet終了を通知
  AT->>Store: 全テキストデータを取得
  Store-->>AT: 　
  AT->>OpenAI-API: 全テキストデータの要約依頼
  OpenAI-API->>AT: 　
  AT->>GDocs-API: 要約Googleドキュメント作成
  GDocs-API-->>AT: 　
  AT->>ChromeExt: 要約GoogleドキュメントURL表示
  AT->>Store: 対象MeetURLの全テキストデータ削除
  Store->>AT: 　
  User->>ChromeExt: MeetURLから離れる
  ChromeExt->>AT: Websocketサーバへ接続終了
```
