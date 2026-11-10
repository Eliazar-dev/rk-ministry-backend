# DEVIN.md — Richard Kwanya Snr Ministry website

Instructions for initializing, running and deploying this project. Follow the sections in order.
Do not change the product behaviour described in **§1** without asking the owner.

> **Prompt to paste into Devin:**
> "Read DEVIN.md fully. Set up the repo, get backend tests and the frontend build passing, then deploy both to Vercel
> following §6. Ask me for the secrets listed in §4 instead of inventing them. When done, run the checklist in §7 and
> report each item as pass/fail."

---

## 1. What this is

Ministry website: video sermons (YouTube embeds), Sabbath School lessons (PDF + video), devotionals, blogs, literature,
medical missionary, children's stories, e-books, mission gallery, a store (cart → M-Pesa STK push → emailed receipt),
donations, prayer requests, contact form, likes + comments on videos/lessons/devotionals, and an admin to manage it all.

**Non-negotiable behaviour**
- **Homepage and navigation are publicly accessible** (visitors can browse the site without an account).
- **Viewing content details, store, donations, contact, and profile require login** (redirects to auth page).
- **Sign-up requires an emailed 6-digit code (OTP).** The account is only created after the code is confirmed.
- **Log in** with email+password, **or** an emailed code, **or** "Continue with Google".
- After a *new* account is created (OTP or Google) a welcome popup shows, then redirects after **3 seconds**.
- Theme: navy + gold. Navbar is **not sticky** and sits on top of the home video carousel.
- Mobile: hamburger drawer slides from the right. Cards: **2 per row on phones, 3 on desktop**. Skeleton loaders while data loads.
- Footer text: `Richard Kwanya Snr #Babawa`. Carousel text: `Equipping people, transforming lives`.

## 2. Repo layout

you have both folders both backend and frontend in same directorty.

```
repo/
├── DEVIN.md
├── frontend/   React 18 + Vite + react-router + lucide-react        → Vercel project #2
│   ├── src/api/{http.js,client.js}      fetch wrapper (JWT + refresh), list() hook, demo-data fallback
│   ├── src/context/{AuthContext,CartContext}.jsx
│   ├── src/components/                  Navbar, HeroCarousel, Cards, VideoModal, OtpCard, GoogleButton, …
│   ├── src/pages/                       Home, Auth, Recover, ResourcePage, Store, Cart, Checkout, Donate, …
│   ├── src/data/mock.js                 demo content (used only when VITE_API_URL is empty)
│   └── vercel.json                      SPA rewrite
└── backend/    Django 5 + DRF + SimpleJWT                          → Vercel project #1
    ├── config/                          settings.py, urls.py, wsgi.py (exposes `app` for Vercel)
    ├── accounts/                        custom email User, EmailOTP, OTP + Google + password-reset views
    ├── content/                         models/admin/API for all content, likes, comments; `seed_demo` command
    ├── shop/                            products, orders, donations, M-Pesa (mpesa.py), receipt emails
    ├── monitoring/                      health monitoring (Heartbeat model, /api/status/ endpoint, admin panel)
    ├── templates/admin/                 admin branding and health panel overrides
    └── vercel.json                      @vercel/python build → config/wsgi.py
```

Frontend **demo mode**: if `VITE_API_URL` is empty the site runs on built-in sample data with fake local accounts
(OTP code is always `123456`). Use it for UI work only — Google sign-in, password reset and payments need the real API.

## 3. Initialize locally

Requirements: Python 3.11+, Node 18+ (20 recommended), npm.

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                     # optional locally; defaults work with SQLite
export DEBUG=1                                           # local only
python manage.py migrate
python manage.py createsuperuser                         # email + password; this is the /admin/ login
python manage.py seed_demo                               # optional starter content
python manage.py test                                    # MUST pass (18 tests)
python manage.py runserver                               # http://127.0.0.1:8000  (admin at /admin/)
```
Without `EMAIL_HOST_USER`, emails (OTP codes, receipts, reset links) **print in the server terminal** — read the code there.

**Frontend**
```bash
cd frontend
cp .env.example .env        # set VITE_API_URL=http://127.0.0.1:8000/api  (and VITE_GOOGLE_CLIENT_ID if you have one)
npm install
npm run dev                 # http://localhost:5173
npm run build               # MUST succeed
```
Local CORS already allows `http://localhost:5173`.

## 4. Accounts / secrets the owner must provide

Ask the owner for these. Never commit them. Never invent values.

| Service | What to create | Gives you |
|---|---|---|
| **Postgres** (Neon / Supabase / Vercel Postgres) | A database. Vercel cannot persist SQLite. | `DATABASE_URL` |
| **Cloudinary** | Account (cloud name `gfiqfk7x` is already used for the logo) → Dashboard → API keys | `CLOUDINARY_URL=cloudinary://KEY:SECRET@CLOUD` |
| **Google OAuth** | See §5.1 | `GOOGLE_CLIENT_ID` |
| **Email sender** | See §5.2 | `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` |
| **M-Pesa Daraja** | See §5.3 (optional until going live; app runs in simulate mode without it) | `MPESA_*` |
| **Django secret** | `python -c "import secrets;print(secrets.token_urlsafe(64))"` | `SECRET_KEY` |

### Backend environment variables (Vercel → backend project → Settings → Environment Variables)

| Variable | Value |
|---|---|
| `SECRET_KEY` | long random string (required in production) |
| `DEBUG` | `0` (or leave unset) |
| `DATABASE_URL` | Postgres URL (SSL is required automatically when `DEBUG` ≠ 1) |
| `ALLOWED_HOSTS` | `.vercel.app,localhost,127.0.0.1` + any custom domain |
| `CSRF_TRUSTED_ORIGINS` | `https://*.vercel.app` + `https://your-domain` (needed for `/admin/` login) |
| `CORS_ALLOWED_ORIGINS` | the **frontend** origin(s), comma-separated, no trailing slash, e.g. `https://rk-ministry.vercel.app,https://www.yourdomain.org` |
| `FRONTEND_URL` | frontend origin (used in password-reset email links) |
| `CLOUDINARY_URL` | from Cloudinary |
| `GOOGLE_CLIENT_ID` | same ID as the frontend's |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP login; `EMAIL_HOST` (default `smtp.gmail.com`), `EMAIL_PORT` (default `587`) |
| `DEFAULT_FROM_EMAIL` | e.g. `Richard Kwanya Snr Ministry <you@gmail.com>` (Gmail requires it to match the login address) |
| `MPESA_ENV` | `sandbox` or `production` |
| `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`, `MPESA_SHORTCODE`, `MPESA_PASSKEY` | from Daraja |
| `MPESA_CALLBACK_URL` | `https://<backend>.vercel.app/api/mpesa/callback/` |

### Frontend environment variables (Vercel → frontend project)

| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://<backend>.vercel.app/api` (include `/api`, no trailing slash) |
| `VITE_GOOGLE_CLIENT_ID` | same Google client ID |
| `VITE_WHATSAPP_NUMBER` | digits only with country code, e.g. `2547XXXXXXXX` |
| `VITE_LOGO_URL` | optional; defaults to the Cloudinary logo URL. `/logo.jpg` is bundled as an automatic fallback |

`VITE_*` values are baked in at **build time** — redeploy the frontend after changing any of them.

## 5. Third-party setup

### 5.1 Google sign-in
1. https://console.cloud.google.com → create/select a project.
2. **APIs & Services → OAuth consent screen**: User type *External*; app name "Richard Kwanya Snr Ministry"; support email; save.
   Keep status *Testing* and add test users until ready, then **Publish app** (otherwise only test users can sign in).
3. **Credentials → Create credentials → OAuth client ID → Web application.**
   - **Authorized JavaScript origins**: `http://localhost:5173`, `https://<frontend>.vercel.app`, and any custom domain.
   - No redirect URI is needed (Google Identity Services button + ID token).
4. Copy the **Client ID** into `GOOGLE_CLIENT_ID` (backend) **and** `VITE_GOOGLE_CLIENT_ID` (frontend).

How it works: the browser gets a Google ID token → `POST /api/auth/google/` → Django verifies it with Google's keys and
checks the audience equals `GOOGLE_CLIENT_ID` and `email_verified` is true → creates or finds the user → returns our JWTs.
A Google email that already has a password account is linked to it (same email = same member).

### 5.2 Email (OTP codes, receipts, password reset)
OTP sign-up cannot work without a real sender in production.
- **Gmail (quickest):** enable 2-Step Verification → create an **App password** → `EMAIL_HOST_USER=you@gmail.com`,
  `EMAIL_HOST_PASSWORD=<16-char app password>`, `DEFAULT_FROM_EMAIL` = same Gmail address. Limit ≈ 500 mails/day.
- **Better for production:** Brevo, Resend or SendGrid SMTP (set `EMAIL_HOST`, `EMAIL_PORT`, user, password; verify a sending domain
  so codes don't land in spam).

### 5.3 M-Pesa Daraja (STK push)
1. https://developer.safaricom.co.ke → create app (Lipa na M-Pesa Sandbox) → copy Consumer Key/Secret; passkey + shortcode `174379` are under *Test credentials*.
2. Set `MPESA_*` vars (§4). The callback URL must be public HTTPS (the deployed backend URL above).
3. **Go-live**: apply for production credentials on Daraja with the ministry's Paybill/Till; set `MPESA_ENV=production`.
   ⚠️ `shop/mpesa.py` sends `TransactionType=CustomerPayBillOnline` (Paybill). For a **Till number** change it to `CustomerBuyGoodsOnline`.
4. Until keys are set the backend is in **simulate mode**: order/donation auto-confirm ~25 s after the "prompt" and a receipt email is sent.
   Remove the simulate shortcut by simply setting the keys — no code change.

## 6. Deploy to Vercel (two projects, same Git repo)

Push the repo to GitHub, then in Vercel **Add New → Project** twice.

**A. Backend first**
- Root Directory: `backend` · Framework Preset: *Other* · leave build/output blank (the `vercel.json` `builds` entry handles it).
- Add all backend env vars (§4). For now set `CORS_ALLOWED_ORIGINS`/`FRONTEND_URL` to a placeholder; fix after step B.
- Deploy. Open `https://<backend>.vercel.app/` → expect `{"status":"ok","service":"rk-ministry-api"}`.
- **Initialize the production database once, from your machine** (Vercel functions are not a place for one-off commands):
  ```bash
  cd backend && source .venv/bin/activate
  export DATABASE_URL='<same Postgres URL as Vercel>'     # do NOT set DEBUG=1 for Neon/Supabase (they need SSL)
  python manage.py migrate
  python manage.py createsuperuser
  python manage.py seed_demo      # optional
  ```

**B. Frontend**
- Root Directory: `frontend` · Framework Preset: *Vite* · Build `npm run build` · Output `dist`.
- Env: `VITE_API_URL=https://<backend>.vercel.app/api`, `VITE_GOOGLE_CLIENT_ID`, `VITE_WHATSAPP_NUMBER`.
- Deploy. `frontend/vercel.json` rewrites all routes to `index.html` so deep links work.

**C. Wire them together**
1. Backend env: `CORS_ALLOWED_ORIGINS=https://<frontend>.vercel.app`, `FRONTEND_URL=https://<frontend>.vercel.app` → **redeploy backend**.
2. Google Console → add `https://<frontend>.vercel.app` to *Authorized JavaScript origins*.
3. Daraja → callback URL = `https://<backend>.vercel.app/api/mpesa/callback/` (and `MPESA_CALLBACK_URL` env).
4. Custom domain? Add it to Vercel, then to `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`, `FRONTEND_URL`, Google origins.

**Vercel limits to remember**
- Request bodies ≈ 4.5 MB: admin PDF/image uploads larger than that fail. Upload big files in Cloudinary directly and paste the URL
  into the `*_url` fields (every upload field has a URL twin).
- Short function timeouts: M-Pesa calls use 8 s timeouts on purpose.
- Admin CSS is served by WhiteNoise with `WHITENOISE_USE_FINDERS=True` (no `collectstatic` step). If `/admin/` ever loads unstyled,
  run `python manage.py collectstatic` locally and commit `staticfiles/` (remove it from `.gitignore`).

## 7. Verification checklist (report pass/fail for each)

Automated
- [ ] `cd backend && python manage.py test` → 31 tests pass (18 original + 13 health monitoring)
- [ ] `cd frontend && npm run build` → succeeds

Deployed (replace hosts)
- [ ] `curl https://<backend>.vercel.app/` → HTML status page with "Backend Status" title (no login required)
- [ ] `curl https://<backend>.vercel.app/api/status/` → `{"status":"ok",...}` (JSON for monitors, no login required)
- [ ] `curl -i https://<backend>.vercel.app/api/sermons/` → **200** (public access for browsing)
- [ ] `/admin/` loads styled; superuser can log in
- [ ] Admin home shows health panel with pulsing green dot, "Backend running", logo, and uptime figures
- [ ] Health panel countdown ticks down and refreshes without page reload; "Refresh now" and Pause/Resume work
- [ ] In the admin add: a Carousel video (Cloudinary mp4 URL), a Sermon (YouTube link + cover), a Lesson (quarter, date range, cover, PDF, YouTube link), a Devotional (with author), a Product → they appear on the site within a refresh
- [ ] **Sign up with a real email**: the 6-digit email arrives, wrong code is rejected, right code creates the account, welcome popup shows ~3 s then lands on Home
- [ ] **Log out → "Email me a login code instead"** works; **password login** works; **Forgot password** email arrives and the link resets it
- [ ] **Continue with Google** works for a new Google account (welcome popup) and again for the same account (no popup)
- [ ] Lesson card: **Watch the lesson** opens that lesson's video page; **Download Pdf** downloads the PDF
- [ ] Like + comment on a sermon → visible in admin **Comments** (untick *Approved* hides it from the site)
- [ ] Store: add to cart → checkout → STK prompt (or simulate) → success page → receipt email; order shows **paid** in admin
- [ ] Donation flow completes and shows in admin **Donations**
- [ ] Phone width (≈375 px): hamburger drawer slides from the right, cards are 2-across, no horizontal scroll; desktop cards 3-across
- [ ] WhatsApp bubble opens `wa.me/<VITE_WHATSAPP_NUMBER>`

## 8. API reference (base `/api`, JSON; `Authorization: Bearer <access>` on everything except where noted)

| Method + path | Auth | Purpose |
|---|---|---|
| `GET /` | public | HTML status page (branded, no login) |
| `GET /status/` | public | HTML status page (branded, no login) |
| `GET /api/status/` | public | JSON health check for uptime monitors (throttled 60/min) |
| `POST /auth/register/` `{name,email,password}` | public | validate + email a code → `{pending:true,email}` (no account yet; 30 s resend cooldown → 429) |
| `POST /auth/verify/` `{email,code}` | public | right code → creates account → `{user,access,refresh,created:true}` |
| `POST /auth/login/` `{email,password}` | public | password login |
| `POST /auth/otp/request/` `{email}` | public | email a login code (always 200; never reveals if the email exists) |
| `POST /auth/otp/login/` `{email,code}` | public | login with code |
| `POST /auth/google/` `{credential}` | public | Google ID token → login or create (`created` flag) |
| `POST /auth/refresh/` `{refresh}` | public | new access token |
| `POST /auth/forgot/`, `POST /auth/reset/` | public | password reset (`uid`,`token`,`password`) |
| `GET /auth/me/` | user | current user |
| `GET /hero /sermons /lessons /devotionals /blogs /literature /medical /children /ebooks /gallery /products` | user | published content |
| `GET /engage/<sermon|lesson|devotional>/<id>/` · `POST …/like/` · `POST …/comments/` `{text}` | user | likes + comments |
| `POST /prayer-requests/`, `POST /contact/` | user | forms |
| `POST /orders/` `{name,email,location,phone,items:[{id,qty}]}` · `GET /orders/<id>/` | user | order + STK push; poll status (`pending|paid|failed`) |
| `POST /donations/` `{amount,phone}` · `GET /donations/<id>/` | user | donation + STK push; poll |
| `POST /mpesa/callback/` | Safaricom | payment result |

OTP rules (in `accounts/otp.py`): 6 digits, valid 10 min, 5 wrong tries then the code is burned, 30 s resend cooldown,
only a keyed hash is stored, a signup code cannot be used for login.

## 9. Admin cheat-sheet (`/admin/`)

| Section | Fields |
|---|---|
| Carousel videos | Cloudinary video URL (mp4), optional poster, order |
| Sermons | title, speaker, date, category, **YouTube link** (auto-embedded), cover (upload or URL) |
| Lessons | title, **quarter**, **date range**, teacher, YouTube link, PDF (upload or URL), **cover** |
| Devotionals | title, **author**, date, scripture, category, excerpt, body, cover |
| Articles | one table for blogs, literature, medical, children, e-books → pick the *section*; e-books take a PDF |
| Gallery photos · Products (name, price KES, cover, description) | |
| Orders · Donations | read-mostly: status, M-Pesa receipt, items |
| Comments | tick/untick **Approved** (moderation) · Prayer requests / Contact messages: mark handled |

## 10. Health monitoring (admin panel)

The Django admin includes a live health monitoring panel at the top of the admin home page (`/admin/`).

**Features:**
- **Public status endpoint**: `GET /api/status/` (no login required) - returns health status for uptime monitors
  - Returns: `{"status": "ok" | "degraded", "database": "ok" | "error", "db_ms": <int>, "time": <ISO timestamp>, "version": <commit sha>}`
  - Throttled to 60 requests/minute per IP
  - Records heartbeat data for uptime calculation
- **Admin health panel**: Visible to staff users on the admin home page
  - Shows live status (green/amber/red pulsing dot)
  - Displays uptime percentages for 24h, 7d, 30d
  - Shows response time, version, and last heartbeat time
  - 24-hour visual timeline of 5-minute blocks
  - Auto-refreshes every 30 seconds with countdown timer
  - Pause/Resume toggle and manual refresh button
  - Timer pauses when browser tab is hidden (Page Visibility API)

**Setting up uptime monitoring:**
For accurate uptime statistics, set up an external uptime monitor:
1. Create a free account at [UptimeRobot](https://uptimerobot.com) (or similar service)
2. Add a new monitor:
   - Type: HTTP(s)
   - URL: `https://<backend-domain>/api/status/`
   - Check interval: 5 minutes
   - Alert contacts: Add email for downtime notifications
3. The monitor will hit the endpoint every 5 minutes, recording heartbeats and providing accurate uptime data

**Optional Vercel Cron:**
If your Vercel plan supports cron jobs, you can add a cron entry to `backend/vercel.json` to call `/api/status/` every 5 minutes automatically. Check Vercel's current documentation for the correct syntax.

**Heartbeat retention:**
- Heartbeats are recorded at most once per minute
- Records older than 35 days are automatically deleted
- Cleanup runs at most once per hour

## 13. Public status page

The backend root (`/`) and `/status/` serve a branded HTML status page showing:
- Live status (pulsing green/amber/red dot)
- Uptime percentages for 24h, 7d, 30d
- Response time and version
- 24-hour visual timeline
- Auto-refresh (30-second countdown with Pause/Resume)

**Access:**
- http://localhost:8000/ (local)
- https://<backend-domain>/ (deployed)
- No login required

**JSON endpoint for monitors:**
- `/api/status/` returns JSON for uptime monitoring services
- Throttled to 60 requests/minute per IP

**Setting up uptime monitoring:**
For accurate uptime statistics, set up an external uptime monitor:
1. Create a free account at [UptimeRobot](https://uptimerobot.com) (or similar service)
2. Add a new monitor:
   - Type: HTTP(s)
   - URL: `https://<backend-domain>/api/status/`
   - Check interval: 5 minutes
   - Alert contacts: Add email for downtime notifications
3. The monitor will hit the endpoint every 5 minutes, recording heartbeats and providing accurate uptime data

**Heartbeat retention:**
- Heartbeats are recorded at most once per minute
- Records older than 35 days are automatically deleted
- Cleanup runs at most once per hour

## 14. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Browser console: CORS error | `CORS_ALLOWED_ORIGINS` missing the exact frontend origin (scheme+host, no trailing `/`) → fix + redeploy backend |
| `/admin/` login: "CSRF verification failed" | add the backend/custom origin to `CSRF_TRUSTED_ORIGINS` |
| OTP email never arrives | `EMAIL_HOST_USER/PASSWORD` unset (codes only print in logs) or wrong; check spam; Gmail needs an *app password* |
| Sign-up says "We could not send the code email" (502) | SMTP rejected the login/from address → check credentials and `DEFAULT_FROM_EMAIL` |
| Google button shows "not set up yet" | `VITE_GOOGLE_CLIENT_ID` empty at **build** time → set + redeploy frontend |
| Google popup error `origin_mismatch` | frontend origin not in *Authorized JavaScript origins* |
| Google works but API says "Google sign-in failed" | backend `GOOGLE_CLIENT_ID` differs from the frontend's |
| 500s on every API call after deploy | tables not created → run `migrate` against the production `DATABASE_URL` |
| `OperationalError … SSL` locally | local Postgres without SSL → `export DEBUG=1` |
| Orders stay "pending" forever (real M-Pesa) | `MPESA_CALLBACK_URL` wrong/not public, or sandbox shortcode/passkey mismatch |
| Logo broken | the Cloudinary link failed → `/logo.jpg` fallback is automatic; fix `VITE_LOGO_URL` if needed |

## 15. Known limits (be honest with the owner)

- This codebase was **tested locally** (31 backend tests including health monitoring, production build, a headless-browser pass over sign-up → code → welcome).
  It has **not** been exercised against live Vercel, a real Google client, a real SMTP provider or real Daraja yet — §7 is how you confirm that.
- No rate limiting beyond OTP cooldown/attempt caps and the status endpoint throttling; consider DRF throttling on `/auth/*` before heavy traffic.
- `/api/mpesa/callback/` is unauthenticated (Safaricom does not sign callbacks); it only changes payments whose `CheckoutRequestID` it already knows.
- "Remember me" on the login form is visual only; sessions use JWT (access 12 h, refresh 30 days).
- Health monitoring uptime accuracy depends on regular calls to `/api/status/` (e.g., from UptimeRobot every 5 minutes). Without an external monitor, uptime statistics may not reflect actual downtime.
- Content is demo data until the owner replaces it; footer/contact phone, email and "Kenya" location are placeholders.

## 16. Working rules

- Keep tests green; add a test for any backend behaviour you change. Never commit `.env`, `db.sqlite3`, `node_modules`, `dist`.
- Prices are always read from the database on checkout — never trust prices sent by the browser.
- Don't add anonymous (logged-out) access to any content or API route.
- Keep field names in `content/serializers.py` in sync with the React components (they are a contract).

**Note**: Gallery albums now return `link` field gated for logged-out users. `/api/about/` is public for pastor profile.

## 17. Prompt 2 features (Gallery albums, Cart toast, Pastor bio, Map)

### Gallery Albums
- **Backend**: Album model in content app with title, date, cover (Cloudinary), photos_url (external link), description, location, published
- **API**: `/api/gallery/` returns albums with `link` field gated for logged-out users
- **Frontend**: Gallery page shows album grid (2 per row mobile, 3 desktop) with year badges and "View photos" button
- **Gating**: Logged-out users see lock badge and sign-up prompt; logged-in users open external album in new tab
- **Admin**: Gallery albums section with validation that photos_url must start with https://

### Cart Toast Notifications
- **Frontend**: Toast system (ToastProvider) with navy/gold glass style
- **Behavior**: Shows "Added to your cart" with product thumbnail, name, and "View cart" button
- **Position**: Bottom-center on mobile (above WhatsApp bubble), top-right on desktop
- **Auto-dismiss**: 3 seconds, pauses on hover, slide-in animation

### Pastor Biography
- **Backend**: PastorProfile model (single record) with name, title, photo, short_intro, biography, quote
- **API**: `/api/about/` returns pastor profile or empty object
- **Frontend**: About page shows "Meet the Pastor" section with portrait, name, title, intro, quote, and full biography
- **Admin**: Pastor profile section (only one record allowed)

### Contact Page Map
- **Frontend**: Google Map embed for Baraton University, Eldoret, Kenya
- **Config**: `VITE_MAP_QUERY` env var (default: "Baraton University, Eldoret, Kenya")
- **Buttons**: "Open in Google Maps" and "Get directions" links
- **Style**: Rounded corners with gold border, responsive height (320px mobile, 420px desktop)
