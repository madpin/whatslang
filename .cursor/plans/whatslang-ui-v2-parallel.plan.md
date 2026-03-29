---
name: WhatsLang UI v2 parallel
overview: Reimagine the dashboard as a new UI (v2), keep the existing static app (v1) unchanged, and serve both from the same FastAPI process so operators can switch or compare. The REST API stays single-source; only presentation layers diverge.
todos:
  - id: routing-v2
    content: Add second static mount and routes (/v2/, optional root policy) in api/main.py; document URLs
  - id: scaffold-v2
    content: Scaffold frontend-v2 with Vite + React; build to dist/; entry, router, and auth flow aligned with v1 token/session
  - id: design-v2
    content: Define IA, navigation model, and visual direction for v2 (avoid v1 pain points from prior review)
  - id: implement-v2-core
    content: Implement v2 screens against existing API (chats, bots, sync, stats) with clear labels and accessibility
  - id: cross-links
    content: Add “Classic dashboard” / “New dashboard” links in both UIs; align login redirect targets
  - id: ci-build
    content: Extend CI with npm ci && npm run build in frontend-v2; verify dist/ and both /static and /v2 deploy
---

# Reimagined UI + parallel v1 / v2 operation

## Goals

- **New experience**: A ground-up UI (layout, hierarchy, component patterns, copy) rather than incremental tweaks to the current glassmorphism dashboard.
- **No forced cutover**: **v1** remains at today’s URLs under [`/static/`](api/main.py) (e.g. [`frontend/index.html`](frontend/index.html)). **v2** is added alongside it.
- **One backend**: All behavior continues to use the existing FastAPI routes (`/chats`, `/chats/sync`, `/stats`, auth, etc.); no duplicate business logic in the browser beyond presentation.

## Serving both UIs from one app

Today the app mounts a single directory:

```347:350:api/main.py
# Mount static files for frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path), html=True), name="static")
```

**Proposed shape:**

| Surface | URL base | Source folder |
|--------|-----------|----------------|
| Legacy (v1) | `/static/…` | [`frontend/`](frontend/) (unchanged) |
| New (v2) | `/v2/…` (or `/app/…`) | `frontend-v2/dist/` (built assets) or `frontend-v2/` if zero-build static |

**Implementation notes:**

- Add a **second** `StaticFiles` mount, e.g. `app.mount("/v2", StaticFiles(directory=..., html=True), name="frontend_v2")`.
- Configure Vite `base: '/v2/'` so asset URLs resolve under the second mount; use `BrowserRouter` with `basename="/v2"` (or HashRouter if you prefer zero server fallback config).
- Ensure the [cache middleware](api/main.py) also treats `/v2/` like `/static/` for `Cache-Control` (or duplicate the prefix check).
- **Root `/`**: Keep current behavior (redirect to login or `index.html`) **or** introduce `DEFAULT_DASHBOARD_VERSION=v1|v2` so production can default to v2 while `/static/index.html` remains reachable. Document the choice in README; avoid breaking bookmarks.
- **Login flow**: [`frontend/login.html`](frontend/login.html) posts to auth and lands on `index.html`. v2 needs an entry (e.g. `login-v2.html` under v2 or shared login page with `?next=/v2/`) so both apps receive `sessionStorage` / same token behavior as today ([`check-auth.js`](frontend/check-auth.js) pattern).

## Reimagined UI (direction — to refine during design)

High-level principles (inherits lessons from the earlier UI review: Bots view state, duplicate sync controls, icon-only actions):

- **Obvious primary tasks**: Sync from WhatsApp, browse chats, start/stop bots, inspect logs — each with **text + icon**, consistent naming.
- **Clear information architecture**: e.g. **Overview** (stats + health) vs **Chats** (list-first) vs **Bots** (flattened or scoped) — avoid two nav items that show the same list unless intentional and labeled.
- **Accessible defaults**: `aria-label` / focus order / reduced reliance on emoji-only buttons.
- **Tech choice (locked)**: **Vite + React** in `frontend-v2/` with `npm run build` producing `frontend-v2/dist/` for the `/v2` static mount. Use the existing API via `fetch` (same-origin) and mirror auth behavior from v1 (`sessionStorage` token + `/auth/status`).

## Cross-linking

- v1: footer or top-bar link “Try new dashboard” → `/v2/` (or `/v2/index.html` depending on mount).
- v2: persistent “Classic dashboard” → `/static/index.html`.
- Same auth: logging out from either clears `sessionStorage` and redirects to the appropriate login page, or a **single** login page with `redirect` query param.

## CI / deployment

- Build v2 if it uses a bundler (`npm ci && npm run build` → `frontend-v2/dist`).
- Ensure Docker/deploy image copies **both** `frontend/` and `frontend-v2/dist` (or equivalent).
- Optional: smoke test `GET /v2/` and `GET /static/index.html` in [`verify_deployment.sh`](verify_deployment.sh) or CI.

## Out of scope (unless you add later)

- Feature flags per user (A/B) — can be env-only first.
- Retiring v1 — only after v2 is validated.

## References

- Legacy app: [`frontend/index.html`](frontend/index.html), [`frontend/app.js`](frontend/app.js).
- API mount: [`api/main.py`](api/main.py).
