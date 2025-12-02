# Separate Model Configuration - Implementation Summary

## Changes Made

### 1. Updated LLMService (`core/llm_service.py`)

**Added Parameters**:
- `vision_model` (Optional[str]): Model to use for image/vision tasks
- `audio_model` (Optional[str]): Model to use for audio transcription (Whisper)

**Behavior**:
- If `vision_model` is not provided, falls back to main `model`
- If `audio_model` is not provided, defaults to `"whisper-1"`
- Logs all three models on initialization for visibility

**Code Changes**:
```python
def __init__(
    self, 
    api_key: str, 
    model: str = "gpt-5", 
    base_url: Optional[str] = None,
    vision_model: Optional[str] = None,
    audio_model: Optional[str] = None
):
    # ... initialization code ...
    self.model = model
    self.vision_model = vision_model or model
    self.audio_model = audio_model or "whisper-1"
```

- `call_with_image()` now uses `self.vision_model`
- `transcribe_audio()` now uses `self.audio_model`

### 2. Updated Main API (`api/main.py`)

**New Environment Variables Loaded**:
```python
OPENAI_VISION_MODEL = os.environ.get('OPENAI_VISION_MODEL', openai_config.get('vision_model'))
OPENAI_AUDIO_MODEL = os.environ.get('OPENAI_AUDIO_MODEL', openai_config.get('audio_model', 'whisper-1'))
```

**LLMService Initialization Updated**:
```python
llm_service = LLMService(
    api_key=OPENAI_API_KEY,
    model=OPENAI_MODEL,
    base_url=OPENAI_BASE_URL,
    vision_model=OPENAI_VISION_MODEL,
    audio_model=OPENAI_AUDIO_MODEL
)
```

**Enhanced Logging**:
Now logs all three models on startup:
```
LLM service initialized (model: gpt-4, vision: gpt-4o, audio: whisper-1)
```

### 3. Updated Environment Template (`env.example`)

Added new optional configuration:

```bash
# Separate models for specific features (optional)
# If not set, OPENAI_MODEL will be used for vision
# Vision models: gpt-4-vision-preview, gpt-4o, gpt-4o-mini, etc.
OPENAI_VISION_MODEL=gpt-4o

# Audio/Whisper model (defaults to whisper-1 if not set)
# Standard Whisper model: whisper-1
OPENAI_AUDIO_MODEL=whisper-1
```

## Usage

### Setting Up Separate Models

Add to your `.env` file:

```bash
# Main model for text translation
OPENAI_MODEL=gpt-4-mini

# Vision model for image processing
OPENAI_VISION_MODEL=gpt-4o

# Audio model for transcription
OPENAI_AUDIO_MODEL=whisper-1
```

### Model Recommendations

**For Vision (Images)**:
- `gpt-4o` - Best quality, more expensive
- `gpt-4o-mini` - Good quality, cost-effective
- `gpt-4-vision-preview` - Older model, still capable

**For Text Translation**:
- `gpt-4-mini` - Fast and cheap
- `gpt-4` - Higher quality
- `gpt-4-turbo` - Fast and high quality

**For Audio**:
- `whisper-1` - Standard (only option for OpenAI Whisper)

### Cost Optimization Examples

**Low Cost Setup**:
```bash
OPENAI_MODEL=gpt-4o-mini           # Text: cheap
OPENAI_VISION_MODEL=gpt-4o-mini    # Images: cheap
OPENAI_AUDIO_MODEL=whisper-1       # Audio: fixed price
```

**Balanced Setup**:
```bash
OPENAI_MODEL=gpt-4o-mini           # Text: cheap (most frequent)
OPENAI_VISION_MODEL=gpt-4o         # Images: high quality (less frequent)
OPENAI_AUDIO_MODEL=whisper-1       # Audio: fixed price
```

**High Quality Setup**:
```bash
OPENAI_MODEL=gpt-4                 # Text: high quality
OPENAI_VISION_MODEL=gpt-4o         # Images: best quality
OPENAI_AUDIO_MODEL=whisper-1       # Audio: fixed price
```

## Troubleshooting Images and Audio

### Issue: Images and Audio Not Being Processed

**Possible Causes**:

1. **Media Type Field Name Mismatch**
   - WhatsApp API might use different field names
   - Check: `type`, `messageType`, `mediaType`, `media`, etc.

2. **Field Not Present in Response**
   - WhatsApp API might not include media type in message objects
   - Media info might be in a nested structure

3. **Different Media Type Values**
   - API might use different strings: "IMAGE", "AUDIO", "DOCUMENT", etc.

### Debugging Steps

#### Step 1: Add Debug Logging

Edit `bots/translation_bot.py` and add at the start of `process_message()`:

```python
def process_message(self, message: Dict[str, Any], history: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    # DEBUG: Log full message structure
    import json
    logger.info(f"[{self.NAME}] DEBUG - Full message: {json.dumps(message, indent=2, default=str)}")
    
    media_type = message.get("media_type")
    message_id = message.get("id")
    logger.info(f"[{self.NAME}] DEBUG - media_type={media_type}, message_id={message_id}")
    # ... rest of method
```

#### Step 2: Send Test Messages

1. Start the bot
2. Send an image to WhatsApp
3. Send a voice message to WhatsApp
4. Check the logs for the DEBUG output
5. Look for the actual field names and values

#### Step 3: Check WhatsApp API Documentation

Check the go-whatsapp-web-multidevice API response format:
- Look at `/chat/{id}/messages` endpoint response
- Check what fields are included for media messages
- Note: Different WhatsApp implementations use different field names

#### Step 4: Alternative Field Names to Try

If `media_type` doesn't work, try these in `translation_bot.py`:

```python
# Try multiple possible field names
media_type = (
    message.get("media_type") or
    message.get("mediaType") or
    message.get("type") or
    message.get("messageType") or
    message.get("message", {}).get("type")
)
```

#### Step 5: Check for Media Indicators

Some APIs indicate media differently:

```python
# Check if message has media indicators
has_image = (
    message.get("hasMedia") and message.get("mimetype", "").startswith("image/")
) or message.get("type") == "image"

has_audio = (
    message.get("hasMedia") and message.get("mimetype", "").startswith("audio/")
) or message.get("type") == "audio" or message.get("type") == "ptt"
```

### Common WhatsApp API Message Structures

**go-whatsapp-web-multidevice** might use:
```json
{
  "id": "message_id",
  "type": "image",  // or "audio", "ptt", "document"
  "content": "caption text",
  "mimetype": "image/jpeg",
  "hasMedia": true
}
```

Or:
```json
{
  "id": "message_id",
  "message": {
    "conversation": "text",
    "imageMessage": { ... },
    "audioMessage": { ... }
  }
}
```

### Quick Fix: Universal Media Detection

Replace the media type detection in `process_message()` with:

```python
def process_message(self, message: Dict[str, Any], history: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    message_id = message.get("id")
    
    # Try multiple ways to detect media type
    media_type = None
    
    # Method 1: Direct media_type field
    if "media_type" in message:
        media_type = message["media_type"]
    
    # Method 2: type field
    elif "type" in message and message["type"] != "text":
        media_type = message["type"]
    
    # Method 3: Check for nested message types
    elif "message" in message:
        msg_obj = message["message"]
        if "imageMessage" in msg_obj:
            media_type = "image"
        elif "audioMessage" in msg_obj or "pttMessage" in msg_obj:
            media_type = "audio"
    
    # Method 4: Check mimetype
    elif "mimetype" in message:
        mime = message["mimetype"]
        if mime.startswith("image/"):
            media_type = "image"
        elif mime.startswith("audio/"):
            media_type = "audio"
    
    logger.info(f"[{self.NAME}] Detected media_type={media_type} for message {message_id}")
    
    # Handle IMAGE messages
    if media_type and "image" in media_type.lower():
        logger.info(f"[{self.NAME}] Processing image message {message_id}")
        return self._process_image_message(message)
    
    # Handle AUDIO/VOICE messages
    if media_type and any(x in media_type.lower() for x in ["audio", "voice", "ptt"]):
        logger.info(f"[{self.NAME}] Processing audio message {message_id}")
        return self._process_audio_message(message)
    
    # Handle TEXT messages
    # ... rest of method
```

## Next Steps

1. **Restart the service** to load the new model configurations
2. **Add debug logging** as shown above
3. **Send test messages** (image and audio) to WhatsApp
4. **Check logs** to see the actual message structure
5. **Adjust media detection** based on what you find in the logs
6. **Test again** with adjusted code

## Verification

After restarting, check the startup logs for:
```
LLM service initialized (model: gpt-4-mini, vision: gpt-4o, audio: whisper-1)
```

This confirms the separate models are loaded correctly.

