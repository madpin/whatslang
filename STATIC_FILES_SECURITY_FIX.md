# Dashboard Security Fix

## Problem

Previously, anyone could access the dashboard and make API calls without authentication, bypassing the password protection completely.

## Root Cause

1. Static files (HTML/JS/CSS) were publicly accessible, but contained no sensitive data
2. **The real issue**: API endpoints were not protected, allowing unauthenticated API calls
3. Frontend didn't include authentication tokens in API requests

## Solution Implemented

This follows the standard **Single Page Application (SPA)** security model:

1. ✅ Static files are publicly accessible (they're just UI code)
2. ✅ JavaScript checks authentication and redirects to login (`check-auth.js`)
3. ✅ **API endpoints are protected** - this is where the actual security is
4. ✅ All API requests include Bearer token

### 1. Backend API Protection (api/main.py)

Added `protect_api_endpoints` middleware that:
- Protects all API endpoints when `DASHBOARD_PASSWORD` is set
- Allows public access to:
  - Static files (protection handled by JavaScript)
  - Auth endpoints (`/auth/verify`, `/auth/status`)
  - Health check endpoints
  - Root endpoint
- Requires valid `Bearer` token in `Authorization` header for all other endpoints
- Returns 401 Unauthorized if token is missing or invalid

```python
@app.middleware("http")
async def protect_api_endpoints(request: Request, call_next):
    """Protect API endpoints with authentication when password is set."""
    dashboard_password = os.getenv("DASHBOARD_PASSWORD", "")
    
    if dashboard_password:
        public_paths = [
            "/", "/favicon.ico", "/health", "/ready",
            "/auth/verify", "/auth/status",
            "/docs", "/redoc", "/openapi.json",
        ]
        
        # Allow static files (JS will handle auth check)
        if request.url.path.startswith("/static/"):
            return await call_next(request)
        
        # Protect all non-public endpoints
        if not any(request.url.path == p for p in public_paths):
            if not await AuthMiddleware.verify_token(request):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required"}
                )
    
    return await call_next(request)
```

### 2. Frontend Authentication (frontend/app.js)

Added `authenticatedFetch()` helper function that:
- Wraps the native `fetch()` API
- Automatically includes the Bearer token from `sessionStorage`
- Ensures all API requests include authentication

```javascript
async function authenticatedFetch(url, options = {}) {
    const authToken = sessionStorage.getItem('auth_token');
    const fetchOptions = { ...options };
    
    if (authToken) {
        fetchOptions.headers = {
            ...fetchOptions.headers,
            'Authorization': `Bearer ${authToken}`
        };
    }
    
    return fetch(url, fetchOptions);
}
```

All `fetch()` calls in the application were replaced with `authenticatedFetch()`.

## Security Flow

### Initial Page Load
1. User visits `/static/index.html` in browser
2. Static HTML file is served (no auth check needed)
3. `check-auth.js` runs immediately on page load
4. If no auth token in sessionStorage → **redirect to `/static/login.html`**
5. If auth token exists → page displays normally

### API Requests
1. JavaScript makes API call using `authenticatedFetch()`
2. Request includes `Authorization: Bearer TOKEN` header
3. Backend middleware checks token
4. If valid → API responds with data
5. If invalid → 401 Unauthorized

### Why This Works
- **Static files (HTML/CSS/JS)**: Not sensitive, can be public
  - JavaScript immediately checks auth and redirects if needed
  - Provides smooth user experience
- **API endpoints**: Contain sensitive data, **must be protected**
  - Can't be accessed without valid Bearer token
  - Even if someone bypasses the JavaScript check, API calls will fail

## Files Modified

- `api/main.py` - Added `protect_api_endpoints` middleware
- `frontend/app.js` - Added `authenticatedFetch()` helper and replaced all fetch calls

## Testing

To test the fix:

1. **Static files (should be accessible):**
   ```bash
   curl http://localhost:8000/static/index.html
   # Should return the HTML (but JavaScript will redirect to login)
   
   curl http://localhost:8000/static/login.html
   # Should return the login page HTML
   ```

2. **API endpoints without authentication (should fail):**
   ```bash
   curl http://localhost:8000/chats
   # Should return: {"detail":"Authentication required"}
   
   curl http://localhost:8000/bots
   # Should return: {"detail":"Authentication required"}
   ```

3. **API endpoints with authentication (should work):**
   ```bash
   # First login to get token
   TOKEN=$(curl -X POST http://localhost:8000/auth/verify \
     -H "Content-Type: application/json" \
     -d '{"password":"your_password"}' | jq -r '.token')
   
   # Then access protected API endpoints
   curl http://localhost:8000/chats \
     -H "Authorization: Bearer $TOKEN"
   # Should return the chats data
   
   curl http://localhost:8000/bots \
     -H "Authorization: Bearer $TOKEN"
   # Should return the bots data
   ```

4. **Browser test:**
   - Open `http://localhost:8000/static/index.html` directly
   - Should be immediately redirected to login page
   - After login, can access dashboard normally
   - All API calls include the Bearer token automatically

## Notes

- This is a basic token-based authentication system
- In production, consider:
  - Storing tokens in a database or Redis
  - Adding token expiration
  - Implementing refresh tokens
  - Using JWT or similar standard
  - Rate limiting authentication attempts

## Date

November 16, 2025

