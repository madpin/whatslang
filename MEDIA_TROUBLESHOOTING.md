# Image and Audio Features - Troubleshooting Guide

## ✅ Completed Changes

### 1. Separate Model Configuration
- ✅ Added `OPENAI_VISION_MODEL` environment variable
- ✅ Added `OPENAI_AUDIO_MODEL` environment variable
- ✅ Updated `LLMService` to support separate models
- ✅ Updated `env.example` with documentation
- ✅ Enhanced startup logging to show all three models

### 2. Improved Media Detection
- ✅ Updated `TranslationBot.process_message()` with robust media type detection
- ✅ Now tries 4 different methods to detect media:
  1. `media_type` field
  2. `type` field
  3. Nested `message.imageMessage/audioMessage` objects
  4. `mimetype` field
- ✅ Added detailed logging for media detection

## 📋 Required Actions

### Step 1: Update Your .env File

Add these new variables to your `.env` file:

```bash
# Vision model for image processing
OPENAI_VISION_MODEL=gpt-4o

# Audio model for transcription  
OPENAI_AUDIO_MODEL=whisper-1
```

**Important**: Make sure your `OPENAI_API_KEY` has access to:
- Vision API (for gpt-4o or similar vision models)
- Whisper API (for audio transcription)

### Step 2: Restart the Service

```bash
# Stop the current service (Ctrl+C or kill the process)
# Then restart:
python run.py
```

### Step 3: Verify Model Configuration

Check the startup logs for this line:
```
LLM service initialized (model: gpt-4-mini, vision: gpt-4o, audio: whisper-1)
```

This confirms the separate models are loaded correctly.

### Step 4: Test Media Messages

1. **Send an Image** with text to your WhatsApp chat
2. **Send a Voice Message** to your WhatsApp chat
3. **Check the logs** for media detection messages

## 🔍 Debugging Media Issues

### Check the Logs

Look for these log messages:

**For Images**:
```
[translation] Detected media_type='image' for message XXXXX
[translation] Processing image message XXXXX
[translation] Downloading image from message XXXXX
[translation] Calling vision AI for image analysis
```

**For Audio**:
```
[translation] Detected media_type='audio' for message XXXXX
[translation] Processing audio message XXXXX
[translation] Downloading audio from message XXXXX
[translation] Transcribing audio with Whisper API
```

### If Media Type is Not Detected

If you see:
```
[translation] Detected media_type='None' for message XXXXX
[translation] Processing text message XXXXX
```

This means the WhatsApp API is not providing media type information in the expected format.

**Solution**: Add debug logging to see the actual message structure.

#### Add Debug Logging

Edit `bots/translation_bot.py` and add this at the start of `process_message()`:

```python
def process_message(self, message: Dict[str, Any], history: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    # DEBUG: Log full message structure
    import json
    logger.info(f"[{self.NAME}] DEBUG - Full message keys: {list(message.keys())}")
    logger.info(f"[{self.NAME}] DEBUG - Full message: {json.dumps(message, indent=2, default=str)[:1000]}")  # First 1000 chars
    
    message_id = message.get("id")
    # ... rest of method
```

Then:
1. Restart the service
2. Send a test image or voice message
3. Check the logs for the DEBUG output
4. Share the DEBUG output to help identify the correct field names

### Common WhatsApp API Field Variations

Different WhatsApp API implementations use different field names:

**go-whatsapp-web-multidevice** might use:
- `type` field: "image", "audio", "ptt", "video", "document"
- Nested `message` object with `imageMessage`, `audioMessage`, etc.
- `hasMedia` boolean with `mimetype` field

**WhatsApp Business API** might use:
- `type` field: "image", "audio", "document", "video"
- Separate media endpoints

**wa-automate** might use:
- `type` field: "image", "audio", "ptt"
- `mimetype` field

### If Download Fails

If you see:
```
[translation] Failed to download image
❌ Sorry, I couldn't download the image.
```

**Possible causes**:
1. **WhatsApp API endpoint issue**: The `/message/{id}/download` endpoint might not exist or have different path
2. **Authentication issue**: Check WHATSAPP_API_USER and WHATSAPP_API_PASSWORD
3. **Message ID format**: The message ID might need to be formatted differently
4. **Media expiration**: WhatsApp media has a TTL and might have expired

**Solution**: Check your WhatsApp API documentation for the media download endpoint.

### If Vision/Whisper API Fails

If you see errors like:
```
LLM call error: ...
Vision AI call failed
```

**Possible causes**:
1. **API Key doesn't have access**: Your OpenAI key might not have Vision or Whisper enabled
2. **Model not available**: The model name might be incorrect
3. **LiteLLM proxy issue**: If using LiteLLM, it might not support Vision or Whisper
4. **Rate limiting**: You might have hit API rate limits

**Solutions**:
- **For OpenAI**: Verify your API key has access to gpt-4o and whisper-1
- **For LiteLLM**: Check LiteLLM documentation for Vision and Whisper support
- **For rate limits**: Wait a few minutes and try again

## 📊 Model Recommendations

### Cost-Effective Setup

```bash
OPENAI_MODEL=gpt-4o-mini           # Text: $0.15/1M input tokens
OPENAI_VISION_MODEL=gpt-4o-mini    # Images: $0.15/1M input tokens  
OPENAI_AUDIO_MODEL=whisper-1       # Audio: $0.006/minute
```

### Balanced Setup (Recommended)

```bash
OPENAI_MODEL=gpt-4o-mini           # Text: cheap and fast
OPENAI_VISION_MODEL=gpt-4o         # Images: best quality
OPENAI_AUDIO_MODEL=whisper-1       # Audio: standard
```

### High-Quality Setup

```bash
OPENAI_MODEL=gpt-4-turbo           # Text: high quality
OPENAI_VISION_MODEL=gpt-4o         # Images: best quality
OPENAI_AUDIO_MODEL=whisper-1       # Audio: standard
```

## 🆘 Getting Help

### Provide This Information

When asking for help, provide:

1. **Startup logs** showing model initialization
2. **Message logs** showing media detection
3. **Error logs** if any errors occur
4. **WhatsApp API name/version** you're using
5. **DEBUG output** from the debug logging above

### Example Good Help Request

```
I'm using go-whatsapp-web-multidevice v4.x

Startup logs show:
LLM service initialized (model: gpt-4-mini, vision: gpt-4o, audio: whisper-1)

When I send an image, I see:
[translation] Detected media_type='None' for message XXXXX
[translation] Processing text message XXXXX

DEBUG output shows:
[translation] DEBUG - Full message keys: ['id', 'timestamp', 'fromMe', 'body', 'type']
[translation] DEBUG - Full message: {"id": "...", "type": "imageMessage", "body": "..."}

It looks like the API uses 'type': 'imageMessage' instead of media_type='image'.
```

## ✅ Success Indicators

You'll know it's working when you see:

**For Images**:
```
[translation] Detected media_type='image' for message XXXXX
[translation] Processing image message XXXXX  
[translation] Downloaded decrypted image: Size=123456 bytes
[translation] Calling vision AI for image analysis
[translation] Image analysis successful
```

**For Audio**:
```
[translation] Detected media_type='audio' for message XXXXX
[translation] Processing audio message XXXXX
[translation] Downloaded decrypted audio: Size=234567 bytes
[translation] Transcribing audio with Whisper API
[translation] Transcription successful: 45 characters
```

And you receive the bot's responses in WhatsApp with the transcribed/translated content!

## 📝 Files Modified

1. `/Users/tpinto/madpin/whatslang/core/llm_service.py` - Added separate model support
2. `/Users/tpinto/madpin/whatslang/api/main.py` - Added environment variables and initialization
3. `/Users/tpinto/madpin/whatslang/bots/translation_bot.py` - Improved media detection
4. `/Users/tpinto/madpin/whatslang/env.example` - Added documentation for new variables

## 🎯 Next Steps

1. ✅ Update your `.env` file with the new variables
2. ✅ Restart the service
3. ✅ Verify model configuration in startup logs
4. ✅ Test with image and audio messages
5. ❓ If not working, add DEBUG logging and check the message structure
6. ❓ Share DEBUG output for further assistance

