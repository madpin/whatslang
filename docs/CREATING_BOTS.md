# 🤖 Creating Custom Bots

**Level:** Intermediate | **Time:** 30 minutes

## 📍 Overview

Learn how to create your own WhatsApp bot from scratch. This guide takes you from a simple echo bot to an advanced AI-powered assistant.

---

## Table of Contents

1. [Understanding Bot Basics](#-understanding-bot-basics)
2. [Your First Bot (5 minutes)](#-your-first-bot-5-minutes)
3. [Bot Anatomy](#-bot-anatomy)
4. [Adding AI/LLM Integration](#-adding-aillm-integration)
5. [Advanced Features](#-advanced-features)
6. [Best Practices](#-best-practices)
7. [Examples & Templates](#-examples--templates)

---

## 🧠 Understanding Bot Basics

### What is a Bot?

A bot is a **Python class** that:
- Receives WhatsApp messages
- Processes them (does something with the text)
- Returns a response
- Automatically appears in the dashboard

### The Simplest Bot

```python
class MyBot(BotBase):
    NAME = "my_bot"          # Unique identifier
    PREFIX = "[mybot]"        # Prefix for responses
    
    def process_message(self, message):
        return "Hello!"       # Reply to every message
```

That's it! This bot will reply "Hello!" to every message.

### How Bots Work

```
Message arrives → Bot checks if should respond → Process → Send reply
      ↓                      ↓                      ↓         ↓
  "Hello"           (not from another bot?)   "thinking..."  "[mybot] Hi there!"
```

---

## 🚀 Your First Bot (5 minutes)

Let's create a simple bot that echoes messages back.

### Step 1: Create Bot File

Create a new file `bots/echo_bot.py`:

```python
from typing import Dict, Any, Optional
from core.bot_base import BotBase


class EchoBot(BotBase):
    """A simple bot that echoes back what you say."""
    
    NAME = "echo_bot"
    PREFIX = "[echo]"
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        """Echo the message back."""
        # Get the message text
        msg_text = message.get("content", "")
        
        # Return it back
        return f"You said: {msg_text}"
```

### Step 2: Restart Server

```bash
# Stop server (Ctrl+C)
# Start again
python run.py
```

### Step 3: Test It!

1. Go to dashboard: http://localhost:8000/static/index.html
2. You should see "Echo Bot" card
3. Click **Start**
4. Send a message in WhatsApp: "Hello world"
5. Bot replies: "[echo] You said: Hello world"

🎉 **Congratulations!** You just created your first bot!

---

## 🔬 Bot Anatomy

Let's understand each part of a bot:

### Required Components

```python
from typing import Dict, Any, Optional
from core.bot_base import BotBase


class YourBot(BotBase):
    """
    What your bot does (appears in dashboard).
    """
    
    # === REQUIRED ATTRIBUTES ===
    
    NAME = "your_bot"          # Must be unique
    PREFIX = "[yourbot]"        # Appears in responses
    
    # === REQUIRED METHOD ===
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Process a message and return a response.
        
        Args:
            message: Message dictionary from WhatsApp API
            
        Returns:
            Response string, or None to skip this message
        """
        # Your logic here
        return "response"
```

### Understanding Each Part

#### 1. Class Declaration

```python
class YourBot(BotBase):
```

- Must inherit from `BotBase`
- Use PascalCase naming (e.g., `MyBot`, `TranslationBot`)

#### 2. Docstring

```python
"""
Short description of what your bot does.
Shows up in the dashboard!
"""
```

- First line appears in dashboard
- Keep it concise and clear

#### 3. NAME Attribute

```python
NAME = "your_bot"
```

- **Must be unique** across all bots
- Use snake_case
- Used internally to identify bot
- Shows in URLs and database

#### 4. PREFIX Attribute

```python
PREFIX = "[yourbot]"
```

- Appears at the start of bot responses
- Helps users identify which bot replied
- Format: `[word]` (with square brackets)
- Should be short and meaningful

#### 5. process_message Method

```python
def process_message(self, message: Dict[str, Any]) -> Optional[str]:
```

- **Core bot logic** goes here
- Receives WhatsApp message as dict
- Returns string (will be sent) or None (skip message)
- Called for every new message in the chat

---

## 💬 Message Structure

The `message` parameter contains:

```python
{
    "id": "message-id-123",
    "content": "The actual message text",
    "fromMe": False,
    "timestamp": 1234567890,
    "participant": "phone@s.whatsapp.net",
    # ... other WhatsApp fields
}
```

### Accessing Message Data

```python
def process_message(self, message: Dict[str, Any]) -> Optional[str]:
    # Get message text
    text = message.get("content", "")
    
    # Check if message is from me
    from_me = message.get("fromMe", False)
    
    # Get timestamp
    timestamp = message.get("timestamp")
    
    # Get sender
    sender = message.get("participant", "")
    
    # Your logic here...
    return f"Got: {text}"
```

---

## 🤖 Adding AI/LLM Integration

Most useful bots use AI to generate intelligent responses.

### Using the Built-in LLM Service

Every bot has access to `self.llm`:

```python
def process_message(self, message: Dict[str, Any]) -> Optional[str]:
    msg_text = message.get("content", "")
    
    # Call LLM
    response = self.llm.call(
        system_prompt="You are a helpful assistant",
        user_message=msg_text
    )
    
    return response
```

### Complete Example: Joke Bot

```python
from typing import Dict, Any, Optional
from core.bot_base import BotBase


class JokeBot(BotBase):
    """Generates funny jokes using AI."""
    
    NAME = "joke_bot"
    PREFIX = "[joke]"
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        """Generate a joke based on the message."""
        msg_text = message.get("content", "")
        
        # Create prompt for AI
        system_prompt = (
            "You are a comedian. Generate family-friendly jokes. "
            "Keep jokes short, clever, and appropriate for all ages."
        )
        
        user_prompt = f"Generate a joke about: {msg_text}"
        
        # Get AI response
        joke = self.llm.call(
            system_prompt=system_prompt,
            user_message=user_prompt
        )
        
        return joke
```

### Translation Bot Example

```python
from typing import Dict, Any, Optional
from core.bot_base import BotBase


class TranslationBot(BotBase):
    """Translates between Portuguese and English."""
    
    NAME = "translation_bot"
    PREFIX = "[ai]"
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        """Translate the message."""
        msg_text = message.get("content", "")
        
        # AI prompt for translation
        system_prompt = (
            "You are a translator. Detect if the text is in Portuguese "
            "or English, then translate it to the other language. "
            "Only return the translation, no explanations."
        )
        
        translation = self.llm.call(
            system_prompt=system_prompt,
            user_message=msg_text
        )
        
        return translation
```

---

## 🎯 Advanced Features

### 1. Selective Response (Don't Reply to Everything)

```python
def process_message(self, message: Dict[str, Any]) -> Optional[str]:
    msg_text = message.get("content", "").lower()
    
    # Only respond to messages with trigger word
    if "bot" not in msg_text:
        return None  # Skip this message
    
    # Process only if triggered
    return "You called?"
```

### 2. Command Pattern

```python
def process_message(self, message: Dict[str, Any]) -> Optional[str]:
    msg_text = message.get("content", "").strip()
    
    # Check for commands
    if msg_text.startswith("/help"):
        return self._handle_help()
    elif msg_text.startswith("/joke"):
        return self._handle_joke()
    elif msg_text.startswith("/quote"):
        return self._handle_quote()
    else:
        return None  # Not a command
    
def _handle_help(self) -> str:
    return "Commands: /help, /joke, /quote"

def _handle_joke(self) -> str:
    return self.llm.call(
        "You are a comedian",
        "Tell me a joke"
    )

def _handle_quote(self) -> str:
    return self.llm.call(
        "You provide inspirational quotes",
        "Give me a quote"
    )
```

### 3. Stateful Bot (Remember Context)

```python
class ConversationBot(BotBase):
    """A bot that remembers conversation history."""
    
    NAME = "conversation_bot"
    PREFIX = "[chat]"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store conversation history
        self.conversation_history = []
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        msg_text = message.get("content", "")
        
        # Add user message to history
        self.conversation_history.append(f"User: {msg_text}")
        
        # Create context from history
        context = "\n".join(self.conversation_history[-5:])  # Last 5 messages
        
        # Get AI response with context
        system_prompt = (
            "You are a helpful assistant. Continue the conversation "
            "naturally based on the context provided."
        )
        
        response = self.llm.call(
            system_prompt=f"{system_prompt}\n\nContext:\n{context}",
            user_message=msg_text
        )
        
        # Add bot response to history
        self.conversation_history.append(f"Bot: {response}")
        
        return response
```

### 4. External API Integration

```python
import requests


class WeatherBot(BotBase):
    """Gets weather information."""
    
    NAME = "weather_bot"
    PREFIX = "[weather]"
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        msg_text = message.get("content", "")
        
        # Extract city name (simple approach)
        city = msg_text.replace("weather", "").strip()
        
        if not city:
            return "Please specify a city. Example: weather London"
        
        # Call weather API
        try:
            api_key = os.getenv("WEATHER_API_KEY")
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if response.status_code == 200:
                temp = data["main"]["temp"] - 273.15  # Convert to Celsius
                desc = data["weather"][0]["description"]
                return f"Weather in {city}: {temp:.1f}°C, {desc}"
            else:
                return f"Couldn't find weather for {city}"
                
        except Exception as e:
            self.log(f"Weather API error: {e}")
            return "Sorry, weather service is unavailable"
```

### 5. Rate Limiting (Don't Reply Too Fast)

```python
import time


class RateLimitedBot(BotBase):
    """A bot that doesn't spam responses."""
    
    NAME = "limited_bot"
    PREFIX = "[bot]"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_response_time = 0
        self.min_interval = 30  # Seconds between responses
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        current_time = time.time()
        
        # Check if enough time has passed
        if current_time - self.last_response_time < self.min_interval:
            return None  # Skip this message
        
        # Process message
        msg_text = message.get("content", "")
        response = f"Processed: {msg_text}"
        
        # Update last response time
        self.last_response_time = current_time
        
        return response
```

---

## 💡 Best Practices

### 1. Clear Bot Purpose

```python
# ✅ Good: Focused, single purpose
class SpellCheckBot(BotBase):
    """Checks spelling and grammar in messages."""
    pass

# ❌ Bad: Too many things
class SuperBot(BotBase):
    """Does translation, jokes, weather, math, and more."""
    pass
```

### 2. Meaningful Names

```python
# ✅ Good
NAME = "translation_bot"
PREFIX = "[translate]"

# ❌ Bad
NAME = "bot1"
PREFIX = "[b1]"
```

### 3. Handle Errors Gracefully

```python
def process_message(self, message: Dict[str, Any]) -> Optional[str]:
    try:
        msg_text = message.get("content", "")
        
        # Your logic
        response = self.llm.call("prompt", msg_text)
        
        return response
        
    except Exception as e:
        # Log error
        self.log(f"Error processing message: {e}")
        
        # Return user-friendly message
        return "Sorry, I encountered an error. Please try again."
```

### 4. Add Logging

```python
def process_message(self, message: Dict[str, Any]) -> Optional[str]:
    msg_text = message.get("content", "")
    
    # Log what you're doing
    self.log(f"Processing: {msg_text[:50]}...")
    
    response = self.llm.call("prompt", msg_text)
    
    self.log(f"Generated response: {len(response)} chars")
    
    return response
```

### 5. Validate Input

```python
def process_message(self, message: Dict[str, Any]) -> Optional[str]:
    msg_text = message.get("content", "")
    
    # Validate input
    if not msg_text or len(msg_text.strip()) == 0:
        return None  # Skip empty messages
    
    if len(msg_text) > 1000:
        return "Message too long. Please keep it under 1000 characters."
    
    # Process valid input
    return self._generate_response(msg_text)
```

### 6. Optimize LLM Prompts

```python
# ✅ Good: Clear, specific prompt
system_prompt = (
    "You are a professional translator specializing in "
    "Portuguese-English translation. Translate accurately "
    "while preserving tone and context. Return only the "
    "translation without explanations."
)

# ❌ Bad: Vague prompt
system_prompt = "Translate this"
```

---

## 📋 Bot Templates

### Minimal Bot Template

```python
"""
[Bot Name] - Short description
"""
from typing import Dict, Any, Optional
from core.bot_base import BotBase


class YourBot(BotBase):
    """One-line description for dashboard."""
    
    NAME = "your_bot"
    PREFIX = "[yourbot]"
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        """Process message and return response."""
        msg_text = message.get("content", "")
        
        # Your logic here
        response = f"Echo: {msg_text}"
        
        return response
```

### AI-Powered Bot Template

```python
"""
[Bot Name] - AI-powered assistant
"""
from typing import Dict, Any, Optional
from core.bot_base import BotBase


class AIBot(BotBase):
    """AI-powered assistant for [purpose]."""
    
    NAME = "ai_bot"
    PREFIX = "[ai]"
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        """Process message using AI."""
        msg_text = message.get("content", "")
        
        # Define AI behavior
        system_prompt = (
            "You are a [role]. Your goal is to [purpose]. "
            "Keep responses [style guidelines]."
        )
        
        # Get AI response
        try:
            response = self.llm.call(
                system_prompt=system_prompt,
                user_message=msg_text
            )
            return response
            
        except Exception as e:
            self.log(f"AI error: {e}")
            return "Sorry, I'm having trouble right now."
```

### Command Bot Template

```python
"""
[Bot Name] - Command-based bot
"""
from typing import Dict, Any, Optional
from core.bot_base import BotBase


class CommandBot(BotBase):
    """Responds to specific commands."""
    
    NAME = "command_bot"
    PREFIX = "[cmd]"
    
    COMMANDS = {
        "/help": "Show available commands",
        "/info": "Get bot information",
        "/version": "Show version",
    }
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        """Process commands."""
        msg_text = message.get("content", "").strip()
        
        # Route to command handler
        if msg_text == "/help":
            return self._handle_help()
        elif msg_text == "/info":
            return self._handle_info()
        elif msg_text == "/version":
            return self._handle_version()
        else:
            return None  # Not a command
    
    def _handle_help(self) -> str:
        """Show help message."""
        commands = "\n".join(
            f"{cmd}: {desc}" 
            for cmd, desc in self.COMMANDS.items()
        )
        return f"Available commands:\n{commands}"
    
    def _handle_info(self) -> str:
        """Show bot info."""
        return "I'm a command bot. Use /help to see commands."
    
    def _handle_version(self) -> str:
        """Show version."""
        return "Version 1.0.0"
```

---

## 🧪 Testing Your Bot

### 1. Test Locally First

```python
# test_my_bot.py
from bots.my_bot import MyBot

# Create bot instance
bot = MyBot(chat_jid="test@g.us", db=None, llm=None, whatsapp=None)

# Test with sample message
test_message = {
    "content": "Hello bot",
    "fromMe": False,
    "timestamp": 123456789
}

# Get response
response = bot.process_message(test_message)
print(f"Bot response: {response}")
```

### 2. Test in Dashboard

1. Restart server
2. Check bot appears in dashboard
3. Start the bot
4. Send test messages in WhatsApp
5. Check logs for errors

### 3. Test Edge Cases

```python
# Test empty message
bot.process_message({"content": ""})

# Test very long message
bot.process_message({"content": "x" * 10000})

# Test special characters
bot.process_message({"content": "!@#$%^&*()"})

# Test Unicode
bot.process_message({"content": "Hello 👋 مرحبا 你好"})
```

---

## 🚀 Deployment

### Make Bot Production-Ready

1. **Add error handling** everywhere
2. **Test thoroughly** with real messages
3. **Add logging** for debugging
4. **Document** your bot's behavior
5. **Consider rate limits**
6. **Validate all inputs**

### Example: Production-Ready Bot

```python
"""
Production-ready bot template with all best practices.
"""
import time
from typing import Dict, Any, Optional
from core.bot_base import BotBase


class ProductionBot(BotBase):
    """Professional bot with error handling and logging."""
    
    NAME = "production_bot"
    PREFIX = "[pro]"
    
    # Configuration
    MAX_MESSAGE_LENGTH = 1000
    MIN_RESPONSE_INTERVAL = 30  # seconds
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_response_time = 0
        self.error_count = 0
        self.max_errors = 5
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        """Process message with full error handling."""
        try:
            # Validate message
            msg_text = message.get("content", "")
            if not self._validate_message(msg_text):
                return None
            
            # Check rate limit
            if not self._check_rate_limit():
                self.log("Rate limit: skipping message")
                return None
            
            # Process message
            self.log(f"Processing: {msg_text[:50]}...")
            response = self._generate_response(msg_text)
            
            # Update state
            self.last_response_time = time.time()
            self.error_count = 0  # Reset on success
            
            return response
            
        except Exception as e:
            # Handle errors gracefully
            self.error_count += 1
            self.log(f"Error ({self.error_count}/{self.max_errors}): {e}")
            
            if self.error_count >= self.max_errors:
                self.log("Too many errors, bot may need restart")
            
            return "Sorry, I encountered an error. Please try again later."
    
    def _validate_message(self, msg_text: str) -> bool:
        """Validate message meets requirements."""
        if not msg_text or len(msg_text.strip()) == 0:
            return False
        
        if len(msg_text) > self.MAX_MESSAGE_LENGTH:
            self.log(f"Message too long: {len(msg_text)} chars")
            return False
        
        return True
    
    def _check_rate_limit(self) -> bool:
        """Check if enough time passed since last response."""
        current_time = time.time()
        time_since_last = current_time - self.last_response_time
        return time_since_last >= self.MIN_RESPONSE_INTERVAL
    
    def _generate_response(self, msg_text: str) -> str:
        """Generate AI response with error handling."""
        try:
            system_prompt = "You are a helpful, professional assistant."
            response = self.llm.call(system_prompt, msg_text)
            return response
        except Exception as e:
            self.log(f"LLM error: {e}")
            raise  # Re-raise to be caught by main handler
```

---

## 📚 Next Steps

After creating your bot:

1. **[Deploy to Production](DEPLOYMENT.md)** - Make it live
2. **[Security Guide](SECURITY.md)** - Protect your service
3. **[Contributing](../CONTRIBUTING.md)** - Share your bot with others

---

## 🎉 Examples in the Wild

Check out existing bots for inspiration:

- `bots/translation_bot.py` - Simple AI translation
- `bots/joke_bot.py` - AI joke generation

---

**Happy bot building!** 🤖✨

Need help? Check the [Main README](../README.md) or open an issue on GitHub!

