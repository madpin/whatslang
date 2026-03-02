# 🧪 Testing Your Protected Dashboard

Quick guide to verify that your password protection is working correctly!

## 🚀 Quick Test Procedure

### Step 1: Enable Protection

Add to your `.env` file:
```bash
DASHBOARD_PASSWORD=test123
```

Restart server:
```bash
python run.py
```

### Step 2: Test Scenarios

#### ✅ Test A: Unauthenticated Access

1. Open browser in **Incognito/Private mode**
2. Go to `http://localhost:8000`
3. **Expected Result**: You should see the magical login page
4. **Check**: URL should be `/static/login.html`

**✓ PASS**: Redirected to login  
**✗ FAIL**: Shows dashboard directly

---

#### ✅ Test B: Successful Login

1. On the login page, enter password: `test123`
2. Click "Enter Portal"
3. **Expected Results**:
   - Success animation (✨ Welcome! ✨)
   - Redirect to dashboard
   - Dashboard shows properly
   - Logout button appears in sidebar

**✓ PASS**: Login successful, dashboard accessible  
**✗ FAIL**: Error message or no redirect

---

#### ✅ Test C: Wrong Password

1. On the login page, enter wrong password: `wrong`
2. Click "Enter Portal"
3. **Expected Results**:
   - Shake animation on form
   - Error message: "Invalid password. Try again!"
   - Password field cleared
   - Still on login page

**✓ PASS**: Shows error, stays on login  
**✗ FAIL**: Allows access or crashes

---

#### ✅ Test D: Direct URL Access (Not Logged In)

1. Open new incognito window
2. Try to access directly: `http://localhost:8000/static/index.html`
3. **Expected Result**: Redirected to login page

**✓ PASS**: Can't bypass login  
**✗ FAIL**: Shows dashboard without login

---

#### ✅ Test E: Logout Functionality

1. Login to dashboard
2. Look for logout button in sidebar (bottom, red button with 🚪 icon)
3. Click logout button
4. Confirm logout dialog
5. **Expected Results**:
   - Fade out animation
   - Redirect to login page
   - Can't access dashboard anymore

**✓ PASS**: Logout works, protection restored  
**✗ FAIL**: No logout button or logout doesn't work

---

#### ✅ Test F: Session Persistence

1. Login to dashboard
2. **Refresh page** (F5)
3. **Expected Result**: Still logged in, no redirect

**✓ PASS**: Session persisted  
**✗ FAIL**: Redirected to login on refresh

---

#### ✅ Test G: Session Clearing (Browser Close)

1. Login to dashboard
2. **Close browser completely**
3. Reopen browser
4. Go to `http://localhost:8000`
5. **Expected Result**: Redirected to login (session cleared)

**✓ PASS**: Session cleared on browser close  
**✗ FAIL**: Still logged in after browser restart

---

#### ✅ Test H: Smart Redirect

1. In incognito mode, try to access: `http://localhost:8000/static/index.html`
2. Gets redirected to login
3. Enter correct password and login
4. **Expected Result**: Returns to `index.html`, not `login.html`

**✓ PASS**: Returns to original page  
**✗ FAIL**: Stays on login or goes to wrong page

---

#### ✅ Test I: Disable Protection

1. Edit `.env` and comment out password:
   ```bash
   # DASHBOARD_PASSWORD=test123
   ```
2. Restart server
3. Go to `http://localhost:8000`
4. **Expected Result**: Dashboard shows directly (no login required)

**✓ PASS**: Protection disabled  
**✗ FAIL**: Still shows login page

---

## 🔍 Advanced Testing

### Browser Console Checks

Open DevTools (F12) → Console:

**When not logged in:**
```
🔒 Authentication is REQUIRED for this dashboard
❌ No auth token found, redirecting to login...
```

**When logged in:**
```
🔒 Authentication is REQUIRED for this dashboard
✓ Auth token found, verifying...
✅ User authenticated, access granted
✓ Logout button added to sidebar
```

**When protection disabled:**
```
🔓 No authentication required
```

### Session Storage Check

DevTools → Application → Session Storage:

**When logged in:**
```
auth_token: "randomtokenhere..."
```

**When redirected from another page:**
```
auth_token: "randomtokenhere..."
redirect_after_login: "/static/index.html"
```

### Network Requests Check

DevTools → Network tab:

**On page load (when protected):**
```
GET /auth/status → 200 OK
Response: {"auth_required": true, "configured": true}
```

**On login:**
```
POST /auth/verify → 200 OK (success)
Response: {"success": true, "message": "...", "token": "..."}

POST /auth/verify → 401 Unauthorized (failure)
Response: {"detail": "Invalid password"}
```

## 📊 Test Results Checklist

Mark each test as you complete it:

- [ ] **Test A**: Unauthenticated access redirects to login
- [ ] **Test B**: Correct password allows access
- [ ] **Test C**: Wrong password shows error
- [ ] **Test D**: Can't bypass login with direct URL
- [ ] **Test E**: Logout button works properly
- [ ] **Test F**: Session persists on refresh
- [ ] **Test G**: Session clears on browser close
- [ ] **Test H**: Smart redirect returns to original page
- [ ] **Test I**: Protection can be disabled

### Score Your Results

- **9/9**: 🎉 Perfect! Everything working!
- **7-8/9**: 👍 Good, minor issues
- **5-6/9**: 😐 Needs attention
- **<5/9**: ❌ Something's wrong, check logs

## 🐛 Common Issues & Solutions

### Issue: Login page shows but dashboard also loads
**Solution**: Check that `check-auth.js` is loaded first in `index.html`:
```html
<script src="check-auth.js"></script>
```

### Issue: Logout button doesn't appear
**Solution**: Check browser console for errors. The button is added dynamically by `check-auth.js`.

### Issue: Can't login (button does nothing)
**Solution**: 
1. Check browser console for errors
2. Check network tab for failed requests
3. Verify backend is running
4. Check password in `.env` file

### Issue: Redirects in infinite loop
**Solution**: Clear sessionStorage:
```javascript
// In browser console:
sessionStorage.clear();
location.reload();
```

### Issue: Session doesn't persist on refresh
**Solution**: Make sure you're using `sessionStorage`, not `localStorage` in the code.

### Issue: Still shows dashboard when password is set
**Solution**: 
1. Make sure `.env` file is in project root
2. Restart the server completely
3. Check that `DASHBOARD_PASSWORD` has a value (no trailing spaces)

## 🎯 API Testing (Optional)

### Test Auth Status Endpoint
```bash
curl http://localhost:8000/auth/status
```

Expected response:
```json
{
  "auth_required": true,
  "configured": true
}
```

### Test Login Endpoint
```bash
curl -X POST http://localhost:8000/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"password": "test123"}'
```

Expected response (success):
```json
{
  "success": true,
  "message": "Authentication successful",
  "token": "random-token-here"
}
```

Expected response (wrong password):
```json
{
  "detail": "Invalid password"
}
```

## 📝 Manual Testing Checklist

### Visual Tests

- [ ] Login page has animations
- [ ] Login page has particles
- [ ] Login page has floating orbs
- [ ] Password field has eye icon toggle
- [ ] Submit button has hover effect
- [ ] Error message has shake animation
- [ ] Success shows "✨ Welcome! ✨"
- [ ] Dashboard has logout button (red, bottom of sidebar)
- [ ] Logout button has hover effect

### Functional Tests

- [ ] Can see login page
- [ ] Can toggle password visibility
- [ ] Can submit with Enter key
- [ ] Wrong password shows error
- [ ] Correct password grants access
- [ ] Dashboard loads after login
- [ ] Logout button appears
- [ ] Logout works and redirects
- [ ] Can't access dashboard without login
- [ ] Session persists on refresh
- [ ] Session clears on browser close

## 🚀 Automated Testing (Optional)

Want to automate these tests? Here's a sample Playwright test:

```javascript
// test-auth.spec.js
const { test, expect } = require('@playwright/test');

test('dashboard requires authentication', async ({ page }) => {
  await page.goto('http://localhost:8000');
  
  // Should redirect to login
  await expect(page).toHaveURL(/login.html/);
  
  // Login page should have password field
  await expect(page.locator('#passwordInput')).toBeVisible();
});

test('correct password grants access', async ({ page }) => {
  await page.goto('http://localhost:8000');
  
  await page.fill('#passwordInput', 'test123');
  await page.click('.submit-btn');
  
  // Should redirect to dashboard
  await expect(page).toHaveURL(/index.html/);
  
  // Logout button should appear
  await expect(page.locator('#logoutBtn')).toBeVisible();
});
```

Run with:
```bash
npx playwright test
```

## ✅ Final Verification

After all tests pass, verify:

1. ✓ Login page is beautiful and animated
2. ✓ Authentication works correctly
3. ✓ All pages are protected
4. ✓ Logout functionality works
5. ✓ Session management works
6. ✓ Can enable/disable protection easily

**All tests passing?** 🎉 **Your dashboard is fully protected!**

## 📞 Need Help?

If tests are failing:

1. Check the console logs (F12 → Console)
2. Check the network requests (F12 → Network)
3. Verify `.env` file has correct password
4. Make sure server is running
5. Try clearing browser cache/sessionStorage
6. Review `SECURITY_IMPLEMENTATION.md` for details

**Happy testing!** 🧪🔒✨

