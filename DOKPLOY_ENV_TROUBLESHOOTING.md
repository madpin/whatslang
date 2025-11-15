# Dokploy Environment Variables Troubleshooting

## Common Issue: "Variable is not set" Warning

If you see errors like:
```
The "DB_PASSWORD" variable is not set. Defaulting to a blank string.
```

This means Docker Compose cannot access the environment variables set in Dokploy's UI.

## Root Cause

Dokploy passes environment variables to containers through its own mechanism, but Docker Compose also tries to interpolate variables during the compose file parsing phase. If variables aren't available at that time, you get these warnings.

## Solution Options

### Option 1: Export Variables in Dokploy (Recommended)

In Dokploy UI:

1. Go to your application
2. Navigate to "Settings" → "Environment Variables"
3. Make sure ALL required variables are set:
   - `DB_NAME=whatslang`
   - `DB_USER=whatslang`
   - `DB_PASSWORD=your_secure_password`
   - All other required variables from `env.dokploy.template`
4. **Important**: After adding/changing environment variables, you must:
   - Click "Save"
   - Go to "Advanced" → "Reset" (this recreates containers with new env vars)
   - Then click "Deploy"

### Option 2: Use .env File in Dokploy

If Dokploy supports mounting .env files:

1. Create a `.env` file in your project root with all variables
2. Add to `.gitignore`
3. Upload it via Dokploy's file manager
4. Dokploy should automatically pick it up

### Option 3: Hardcode Defaults (Not Recommended for Production)

For testing only, you can add default values in `docker-compose.dokploy.yml`:

```yaml
POSTGRES_PASSWORD: ${DB_PASSWORD:-temporary_password_CHANGE_THIS}
```

**WARNING**: This is insecure for production. Always use proper secret management.

## Verification Steps

After configuring environment variables:

### 1. Check Container Logs
```bash
# In Dokploy, check logs for postgres container
# Look for successful startup messages
```

### 2. Verify Environment Inside Container
```bash
# In Dokploy's container shell for backend:
echo $DATABASE_URL

# In postgres container:
env | grep POSTGRES
```

### 3. Test Database Connection
```bash
# In backend container:
python -c "from app.database import engine; print(engine.url)"
```

### 4. Check Health Status
```bash
# Via Dokploy UI or direct API call:
curl https://your-domain.com/api/health
```

## Required Environment Variables

These MUST be set for the application to work:

### Database
- `DB_PASSWORD` (required, no default for security)
- `DB_NAME` (default: whatslang)
- `DB_USER` (default: whatslang)

### WhatsApp API
- `WHATSAPP_API_URL` (required)
- `WHATSAPP_API_TOKEN` OR (`WHATSAPP_API_USER` + `WHATSAPP_API_PASSWORD`)

### LLM Provider (at least one)
- `OPENAI_API_KEY` OR `ANTHROPIC_API_KEY`

## Common Mistakes

### 1. Not Redeploying After Changing Env Vars
- Environment variables are only applied during container creation
- You must **redeploy** or **reset** after changing them

### 2. Typos in Variable Names
- Variable names are case-sensitive
- `DB_PASSWORD` ≠ `db_password`

### 3. Spaces in Values
- Don't add spaces around `=`
- ✅ `DB_PASSWORD=secret123`
- ❌ `DB_PASSWORD = secret123`

### 4. Special Characters Not Escaped
- Some special characters need escaping in YAML
- Quote values with special characters: `"my$ecret!pass"`

## Debugging Commands

### Check if postgres is accessible
```bash
# From backend container:
nc -zv postgres 5432
```

### Manual database connection test
```bash
# From backend container:
python <<EOF
import psycopg2
conn = psycopg2.connect(
    host='postgres',
    database='whatslang',
    user='whatslang',
    password='your_password'
)
print("Connection successful!")
conn.close()
EOF
```

### Check Docker Compose interpolation
```bash
# Locally (to see what Docker Compose sees):
docker-compose -f docker-compose.dokploy.yml config
```

## Still Having Issues?

1. **Check Dokploy documentation** for their specific environment variable handling
2. **Enable debug logging**: Set `DEBUG=true` and `LOG_LEVEL=DEBUG`
3. **Check all container logs** in Dokploy UI
4. **Verify network connectivity** between containers
5. **Try recreating the entire stack** (delete and redeploy)

## Security Best Practices

1. ✅ Use strong, randomly generated passwords:
   ```bash
   openssl rand -base64 32
   ```

2. ✅ Use Dokploy's secret management features

3. ✅ Never commit real credentials to git

4. ✅ Rotate credentials regularly

5. ✅ Use different credentials for each environment (dev/staging/prod)

## Contact & Support

If you continue experiencing issues:
- Check the [main README](README.md)
- Review [Dokploy documentation](docs/DOKPLOY_DEPLOYMENT.md)
- Open an issue on GitHub with sanitized logs

