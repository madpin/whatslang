# API Error Handling Improvements

## Problem

The WhatsApp API at `gowa.madpin.dev` was returning **500 Internal Server Error** when fetching messages from certain chats, causing the bot to fail silently with limited diagnostic information.

Example error:
```
Error fetching messages: 500 Server Error: Internal Server Error for url: 
https://gowa.madpin.dev/chat/5511996141038-1487995301@g.us/messages?limit=20&offset=0
```

## Root Cause

The 500 error is a **server-side issue** on the WhatsApp API (`gowa.madpin.dev`), not a client-side bug. This could be caused by:

1. Server-side bugs when processing specific chats
2. Database issues on the API server
3. Authentication/authorization problems with certain groups
4. Temporary resource exhaustion (memory, connections)
5. Network issues between the API server and WhatsApp's backend

## Solutions Implemented

### 1. **Automatic Retry Logic** 

The `get_messages()` method now automatically retries failed requests:

- **Default**: 2 retries with 1 second delay between attempts
- **Smart retry**: Only retries on server errors (5xx) and network issues
- **Skip retry**: Doesn't retry client errors (4xx) except rate limits (429)

```python
# Usage with custom retry settings
messages = whatsapp_client.get_messages(
    chat_jid="5511996141038-1487995301@g.us",
    limit=20,
    max_retries=3,      # Try up to 3 times
    retry_delay=2.0     # Wait 2 seconds between retries
)
```

### 2. **Enhanced Error Logging**

The error handling now captures and logs:

- HTTP status codes
- Response body content (first 500 chars)
- Structured error details from JSON responses
- Attempt count and retry information
- Detailed exception traces

This helps diagnose the actual cause of server errors.

### 3. **Health Check Method**

A new `health_check()` method to verify API connectivity:

```python
if whatsapp_client.health_check():
    print("API is healthy")
else:
    print("API is experiencing issues")
```

### 4. **Optional Chat Validation**

You can now validate that a chat exists before fetching messages:

```python
messages = whatsapp_client.get_messages(
    chat_jid="5511996141038-1487995301@g.us",
    validate_chat=True  # Check chat exists first
)
```

This prevents unnecessary API calls to non-existent or inaccessible chats.

### 5. **Graceful Degradation**

Instead of crashing, the client now:
- Returns an empty list `[]` when messages can't be fetched
- Logs detailed error information for debugging
- Allows the bot to continue operating

## Configuration

New settings in `config.yaml`:

```yaml
api_settings:
  max_retries: 2                    # Number of retry attempts
  retry_delay: 1.0                  # Seconds between retries
  request_timeout: 10               # Request timeout in seconds
  validate_chat_before_fetch: false # Pre-validate chat existence
```

## When to Use Each Feature

### Use Retries (default: enabled)
- For temporary server glitches
- Network hiccups
- Transient 5xx errors

### Use Chat Validation
- When dealing with dynamic/changing chat lists
- If chats are frequently deleted or become inaccessible
- To reduce unnecessary API calls

⚠️ **Note**: Chat validation adds an extra API call before each message fetch

### Use Health Checks
- Before starting bots
- In monitoring/alerting systems
- After detecting multiple failures

## Testing the Fix

1. **Normal operation**: The bot will now automatically retry failed requests
2. **Check logs**: Look for retry attempt messages:
   ```
   Retry attempt 1/2 for get_messages(5511996141038-1487995301@g.us)
   ```
3. **Successful retry**: You'll see:
   ```
   Successfully fetched messages after 1 retries
   ```

## What This Doesn't Fix

This improvement makes the **client more resilient**, but it **cannot fix server-side issues** at `gowa.madpin.dev`. If the server consistently returns 500 errors, you should:

1. **Check the server logs** on `gowa.madpin.dev`
2. **Verify the chat exists** and is accessible
3. **Test the API directly** using curl or Postman:
   ```bash
   curl -u madpin:Senha?gowa123 \
     "https://gowa.madpin.dev/chat/5511996141038-1487995301@g.us/messages?limit=20&offset=0"
   ```
4. **Contact the API maintainer** if the problem persists

## Monitoring

Watch for these log patterns:

### ✅ Successful Recovery
```
HTTP error fetching messages (attempt 1/3): 500 Server Error
Will retry after 1.0s...
Successfully fetched messages after 1 retries
```

### ⚠️ Temporary Issues
```
HTTP error fetching messages (attempt 1/3): 500 Server Error
Response body is empty
```

### ❌ Persistent Problems
```
Failed to fetch messages after 3 attempts. Last error: 500 Server Error
```

If you see persistent failures, investigate the server-side issue.

## Next Steps

1. **Monitor the logs** to see if retries resolve the issue
2. **Adjust retry settings** in `config.yaml` if needed
3. **Enable chat validation** if dealing with unstable chat lists
4. **Investigate server-side** if errors persist after retries

## Related Files

- `core/whatsapp_client.py` - WhatsApp API client with retry logic
- `config.yaml` - Configuration settings
- `api/main.py` - API endpoints that use the client
- `core/bot_base.py` - Bot polling that fetches messages

