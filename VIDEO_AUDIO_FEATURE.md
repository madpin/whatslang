# Video Audio Transcription Feature

## Overview

Successfully implemented video audio transcription and translation for the WhatsApp Translation Bot. The bot can now:

1. **Download video messages** from WhatsApp
2. **Extract audio tracks** using FFmpeg
3. **Transcribe audio** using OpenAI Whisper
4. **Translate transcriptions** between English and Portuguese

## Implementation Summary

### Files Modified

#### 1. `requirements.txt`
- Added `ffmpeg-python==0.2.0` for Python bindings to FFmpeg

#### 2. `nixpacks.toml`
- Added `ffmpeg-full` to nixPkgs array for Dokploy deployment support

#### 3. `core/whatsapp_client.py`
- **New Method**: `download_and_decrypt_video(message_id, chat_jid)`
  - Downloads and decrypts video messages using WhatsApp API
  - Uses `/message/{id}/download` endpoint (same as audio/image)
  - Returns raw video bytes
  - Longer timeout (60s) for larger files

#### 4. `core/llm_service.py`
- **New Method**: `extract_audio_from_video(video_bytes)`
  - Extracts audio track from video files using FFmpeg
  - Writes video to temporary file
  - Converts audio to mp3 format (16kHz, mono, 64k bitrate)
  - Cleans up temporary files automatically
  - Detects videos without audio tracks
  - Returns extracted audio bytes
- **Added Imports**: `ffmpeg`, `os`, `tempfile`

#### 5. `bots/translation_bot.py`
- **Updated**: `process_message()` method
  - Added video detection logic
  - Routes video messages to new handler
  - Checks for `media_type == "video"` and `videoMessage` in nested objects
  
- **New Method**: `_process_video_message(message)`
  - Downloads video using WhatsApp client
  - Validates video size (max 100MB)
  - Extracts audio using FFmpeg
  - Validates extracted audio size (max 25MB for Whisper)
  - Transcribes audio using Whisper API
  - Translates transcription
  - Returns formatted response

#### 6. `MEDIA_FEATURES_IMPLEMENTATION.md`
- Updated overview to include video support
- Added video processing section with capabilities and response format
- Added video-specific test cases
- Documented FFmpeg requirement

#### 7. `env.example`
- Added section documenting FFmpeg requirement
- Installation instructions for various platforms

## Features

### Supported Video Formats
- MP4, MOV, AVI, and other common video formats
- Any format supported by FFmpeg

### Size Limits
- **Video File**: Maximum 100MB
- **Extracted Audio**: Maximum 25MB (Whisper API limit)

### Response Format

When a user sends a video:
```
🎬 Video Audio Transcription:
[transcribed audio from video]

🌍 Translation:
[translated text]
```

### Error Handling

The implementation includes comprehensive error handling:

1. **Videos without audio**: User-friendly message explaining the video has no audio
2. **Large videos**: Clear message about size limit (100MB)
3. **Large audio tracks**: Clear message about Whisper's 25MB limit
4. **Download failures**: User-friendly error messages
5. **Extraction failures**: Catches FFmpeg errors and reports gracefully
6. **Transcription failures**: Handles Whisper API errors

## Usage

### Prerequisites

1. **FFmpeg Installation**:
   - Ubuntu/Debian: `apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Docker/Nixpacks: Automatically installed via nixpacks.toml

2. **Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **OpenAI API Key** with Whisper access

### Deployment

For Dokploy deployment using Nixpacks:
- FFmpeg is automatically installed via `nixpacks.toml`
- No additional configuration needed

### Testing

Send a video message to your WhatsApp bot:

1. **Video with audio**: Bot will transcribe and translate the audio
2. **Video without audio**: Bot will inform you there's no audio
3. **Large video**: Bot will inform you of size limits

## Technical Details

### Audio Extraction Process

1. Video bytes are written to temporary file
2. FFmpeg extracts audio track:
   - Format: MP3
   - Sample rate: 16kHz
   - Channels: Mono
   - Bitrate: 64k
3. Extracted audio is read as bytes
4. Temporary files are cleaned up
5. Audio bytes passed to Whisper API

### Media Type Detection

The bot detects videos using multiple methods:
1. Direct `media_type` field
2. `type` field
3. Nested `message.videoMessage` object
4. MIME type starting with `video/`

This ensures compatibility with different WhatsApp API implementations.

## Performance Considerations

- **Video download**: May take longer for large files (60s timeout)
- **Audio extraction**: Usually fast (< 10 seconds for most videos)
- **Transcription**: Depends on audio length (typically 10-30 seconds)
- **Translation**: Fast (1-3 seconds)

**Total processing time**: Typically 20-60 seconds for standard videos

## Future Enhancements

Possible improvements:
- Support for longer videos (chunking)
- Video preview/thumbnail generation
- Support for multiple audio tracks
- Language detection for better transcription
- Subtitle extraction from video files

## References

- WhatsApp API: [go-whatsapp-web-multidevice](https://github.com/aldinokemal/go-whatsapp-web-multidevice)
- OpenAI Whisper API: [https://platform.openai.com/docs/guides/speech-to-text](https://platform.openai.com/docs/guides/speech-to-text)
- FFmpeg: [https://ffmpeg.org/](https://ffmpeg.org/)
- ffmpeg-python: [https://github.com/kkroening/ffmpeg-python](https://github.com/kkroening/ffmpeg-python)

