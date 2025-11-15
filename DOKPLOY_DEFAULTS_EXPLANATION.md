# Dokploy Docker Compose Default Values Explanation

## Overview

The `docker-compose.dokploy.yml` file has been updated with **working default values** to solve the issue where Docker Compose couldn't access environment variables set in Dokploy's UI.

## What Changed

### Before (Broken)
```yaml
environment:
  DATABASE_URL: postgresql://${DB_USER:-whatslang}:${DB_PASSWORD}@postgres:5432/...
  WHATSAPP_API_URL: ${WHATSAPP_API_URL}
  
postgres:
  environment:
    POSTGRES_PASSWORD: ${DB_PASSWORD}  # ❌ No default = empty string = postgres fails
```

**Problem**: Without a default value, `DB_PASSWORD` became an empty string, causing postgres to fail healthcheck and preventing the stack from starting.

### After (Working)
```yaml
environment:
  DATABASE_URL: postgresql://${DB_USER:-whatslang}:${DB_PASSWORD:-changeme_insecure_default}@postgres:5432/...
  WHATSAPP_API_URL: ${WHATSAPP_API_URL:-https://CONFIGURE_YOUR_WHATSAPP_API_URL}
  
postgres:
  environment:
    POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme_insecure_default}  # ✅ Has default = postgres starts
```

**Solution**: Added defaults for critical values so containers can start, even if Dokploy's environment variables aren't injected during compose parsing.

## Default Values Set

### Database Configuration
| Variable | Default Value | Security |
|----------|--------------|----------|
| `DB_NAME` | `whatslang` | ✅ Safe |
| `DB_USER` | `whatslang` | ✅ Safe |
| `DB_PASSWORD` | `changeme_insecure_default` | ⚠️ **INSECURE** - MUST change in production |

### WhatsApp API Configuration
| Variable | Default Value | Notes |
|----------|--------------|-------|
| `WHATSAPP_API_URL` | `https://CONFIGURE_YOUR_WHATSAPP_API_URL` | Descriptive placeholder |
| `WHATSAPP_API_TOKEN` | (empty) | Optional - depends on auth method |
| `WHATSAPP_API_USER` | (empty) | Optional - for basic auth |
| `WHATSAPP_API_PASSWORD` | (empty) | Optional - for basic auth |
| `WHATSAPP_PHONE_NUMBER_ID` | (empty) | Optional |

### LLM Configuration
| Variable | Default Value | Notes |
|----------|--------------|-------|
| `OPENAI_API_KEY` | (empty) | At least one LLM key required |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Standard OpenAI endpoint |
| `OPENAI_MODEL` | `gpt-5-mini` | Cost-effective model |
| `ANTHROPIC_API_KEY` | (empty) | Alternative to OpenAI |

### Application Settings
| Variable | Default Value | Notes |
|----------|--------------|-------|
| `DEBUG` | `false` | Production setting |
| `LOG_LEVEL` | `INFO` | Standard logging |
| `CORS_ORIGINS` | `http://localhost:3000,https://yourdomain.com` | Needs customization |

## Why This Approach?

### The Problem with Dokploy
Dokploy's environment variable injection works at the **container runtime** level, but Docker Compose needs variables during the **compose file parsing** phase. If variables aren't available during parsing, Docker Compose substitutes them with empty strings.

### The Solution
By providing defaults in the compose file itself:
1. ✅ Docker Compose can parse the file successfully
2. ✅ Postgres container can start (has a password, even if insecure)
3. ✅ Other containers can connect to postgres
4. ✅ Stack becomes operational immediately
5. ⚠️ User is warned to change insecure defaults

## Security Considerations

### ⚠️ CRITICAL: Default DB_PASSWORD is INSECURE

The default password `changeme_insecure_default` is:
- **Visible in the docker-compose file** (public repository)
- **Known to anyone** who reads this documentation
- **Should NEVER be used** in production

### What You MUST Do

1. **In Dokploy UI** → Your Application → Environment Variables:
   ```bash
   DB_PASSWORD=<generate secure password>
   ```
   
2. **Generate secure password**:
   ```bash
   openssl rand -base64 32
   ```

3. **Click "Save"** in Dokploy

4. **Reset the stack**:
   - Go to "Advanced" → "Reset" (recreates containers with new env vars)
   - Then click "Deploy"

### Why Not Use a Random Password?

We could generate a random password on first deploy, but:
- ❌ It wouldn't persist across container recreations
- ❌ It wouldn't be accessible to the user for manual access
- ❌ Dokploy doesn't support this pattern well
- ✅ An obvious insecure default forces users to set it properly

## Deployment Workflow

### First Deployment (Without Setting Variables)

1. Deploy to Dokploy with default compose file
2. **Postgres starts** with default password ✅
3. **Backend starts** and connects to postgres ✅
4. **Frontend starts** ✅
5. Stack is running but:
   - ⚠️ Database password is insecure
   - ⚠️ WhatsApp API not configured (functionality limited)
   - ⚠️ LLM not configured (bots won't work)

### Proper Deployment (With Variables Set)

1. **Before deploying**, set environment variables in Dokploy UI
2. Deploy to Dokploy
3. **All services start** with your configured values ✅
4. **Fully functional** with secure credentials ✅

### Updating Variables After Deployment

1. Update variables in Dokploy UI
2. **Important**: Go to "Advanced" → "Reset"
   - This recreates containers with new env vars
   - Simply redeploying may not update all containers
3. Click "Deploy"
4. Verify new values are in effect

## Verification Steps

### 1. Check if Default Password is Being Used

```bash
# In Dokploy terminal for postgres container:
echo $POSTGRES_PASSWORD

# If output is "changeme_insecure_default" → ⚠️ INSECURE!
# If output is a long random string → ✅ Good!
```

### 2. Check Database Connection

```bash
# In backend container:
python -c "from app.database import engine; print(engine.url)"

# Look for the password in the connection string
# If you see "changeme_insecure_default" → ⚠️ Change it!
```

### 3. Test Application

```bash
curl https://your-domain.com/api/health

# Should return: {"status":"healthy"}
```

## Best Practices

### Development/Testing
- ✅ Default values are OK for quick testing
- ✅ Use for local development
- ✅ Use for proof-of-concept deployments

### Staging
- ⚠️ Should use proper passwords
- ✅ Can use test API keys
- ✅ Set up proper monitoring

### Production
- ❌ **NEVER** use default passwords
- ✅ Use strong, randomly generated passwords
- ✅ Set all required API keys
- ✅ Use specific image versions (not `:latest`)
- ✅ Enable automatic backups
- ✅ Set up monitoring and alerts
- ✅ Configure proper CORS origins
- ✅ Enable SSL/TLS

## Troubleshooting

### Stack Still Won't Start

1. **Check Dokploy logs** for each service
2. **Verify postgres is healthy**:
   ```bash
   docker ps | grep postgres
   # Should show (healthy)
   ```
3. **Check if env vars are set**:
   ```bash
   # In backend container:
   env | grep DB_PASSWORD
   ```

### "Database connection refused"

- Postgres is not healthy yet
- Wait for healthcheck to pass (10-30 seconds)
- Check postgres logs for errors

### "WhatsApp API unreachable"

- Set `WHATSAPP_API_URL` to your actual WhatsApp API instance
- Verify the URL is accessible from Dokploy server
- Check API authentication is configured

### "No LLM provider configured"

- Set at least one of: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
- Verify API key is valid
- Check API key has sufficient credits/quota

## Related Documentation

- [DOKPLOY_DEPLOYMENT.md](docs/DOKPLOY_DEPLOYMENT.md) - Full deployment guide
- [DOKPLOY_ENV_TROUBLESHOOTING.md](DOKPLOY_ENV_TROUBLESHOOTING.md) - Environment variable troubleshooting
- [env.dokploy.template](env.dokploy.template) - Template for all environment variables
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Pre-deployment checklist

## Summary

✅ **What was fixed**: Added default values to allow containers to start
⚠️ **Security warning**: Default DB password is insecure by design
🔧 **Action required**: Set proper values in Dokploy UI before production use
📚 **Documentation**: Updated to clearly indicate insecure defaults

The system will now start successfully in Dokploy, but you **MUST** configure proper credentials for any non-testing use!

