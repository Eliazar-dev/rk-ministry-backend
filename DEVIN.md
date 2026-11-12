# DEVIN.md — Richard Kwanya Snr Ministry website

Instructions for initializing, running and deploying this project. Follow the sections in order.
Do not change the product behaviour described in **§1** without asking the owner.

> **Prompt to paste into Devin:**
> "Read DEVIN.md fully. Set up the repo, get backend tests and the frontend build passing, then deploy both to Vercel
> following §6. Ask me for the secrets listed in §4 instead of inventing them. When done, run the checklist in §7 and
> report each item as pass/fail. **Do not refactor or 'improve' anything that already works** — change only what a
> failing check requires, and tell me exactly which files you touched."

---

## 1. What this is

Ministry website: video sermons (YouTube embeds), Sabbath School lessons (PDF + video), devotionals, blogs, literature,
medical missionary, children's stories, e-books, mission gallery, a store (cart → M-Pesa STK push → emailed receipt),
donations, prayer requests, contact form, likes + comments on videos/lessons/devotionals, a pastor biography, and a
**React admin panel at `/manage`** (Django's `/admin/` still exists as a backup).

**Non-negotiable behaviour**
- **The site is public.** Visitors can open every page and see every card. They are asked to sign up **only when they press
  content** (play a video, download a PDF, read an article, open an album link, checkout, donate, like/comment).
- **The protection is real, not cosmetic.** For logged-out requests the API removes `sermons.youtube`, `lessons.youtube/pdf`,
  `devotionals.body`, `articles.body/pdf` and `albums.link` and returns `"locked": true`. Never expose those to visitors.
- After sign-up the page reopens what the visitor pressed (video/article); downloads and album links show a "tap again" toast.
- Gallery = **albums**: only the cover image is on Cloudinary; the album link points to an outside site (Pixieset, Google Photos…).
- **Sign-up requires an emailed 6-digit code (OTP).** The account is only created after the code is confirmed.
- **Log in** with email+password, **or** an emailed code, **or** "Continue with Google".
- After a *new* account is created (OTP or Google) a welcome popup shows, then redirects after **3 seconds**.
- Theme: navy + gold. Navbar is **not sticky** and sits on top of the home video carousel.
- Mobile: hamburger drawer slides from the right. Cards: **2 per row on phones, 3 on desktop**. Skeleton loaders while data loads.
- Footer text: `Richard Kwanya Snr #Babawa`. Carousel text: `Equipping people, transforming lives`.
- Backend root `/` is a branded **status page** (plain Django view, nothing to do with `/api/`); `/health/` returns JSON.

## 2. Repo layout

Unzip `frontend.zip` and `backend.zip` into one folder so you get:

```
repo/
├── DEVIN.md
├── frontend/   React 18 + Vite + react-router + lucide-react        → Vercel project #2
│   ├── src/config.js                    phone, email, map place (env driven)
│   ├── src/api/{http.js,client.js}      fetch wrapper (JWT + refresh + retry-as-visitor), cached useList(), demo fallback
│   ├── src/context/                     Auth, Cart, Toast ("Added to cart"), Gate (sign-up prompt + resume)
│   ├── src/components/                  Navbar, HeroCarousel, Cards, VideoModal, Engage, OtpCard, GoogleButton, …
│   ├── src/pages/                       Home, Auth, ResourcePage, Reader, About, Contact, Store, Cart, Checkout, Donate, …
│   ├── src/admin/                       React admin panel (lazy-loaded chunk, route /manage): resources.jsx = all field config
│   ├── scripts/sitemap.mjs              writes sitemap.xml + robots.txt at build from VITE_SITE_URL
│   ├── src/data/mock.js                 demo content (used only when VITE_API_URL is empty)
│   └── vercel.json                      SPA rewrite
└── backend/    Django 5 + DRF + SimpleJWT                          → Vercel project #1
    ├── config/                          settings.py, urls.py, wsgi.py (exposes `app` for Vercel)
    ├── accounts/                        custom email User, EmailOTP, OTP + Google + password-reset views
    ├── content/                         models + public API (locked fields for visitors), albums, pastor profile; `seed_demo`
    ├── panel/                           staff-only API `/api/manage/*` for the React admin + Cloudinary upload signing
    ├── monitoring/                      status page `/` + `/health/` (isolated plain views, heartbeat table)
    ├── shop/                            products, orders, donations, M-Pesa (mpesa.py), receipt emails
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
python manage.py createsuperuser                         # email + password; this account signs in to the site and sees /manage
python manage.py seed_demo                               # optional starter content
python manage.py test                                    # MUST pass (43 tests)
python manage.py runserver                               # http://127.0.0.1:8000  (status page at /)
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
**Admin panel:** sign in on the site with the superuser's email/password, then open `/manage` (a gold dashboard icon also
appears in the navbar and on the Profile page for staff). To make someone else an admin: Django `/admin/` → Users → tick *Staff*.

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
| `VITE_CONTACT_PHONE`, `VITE_CONTACT_EMAIL` | shown on Contact + footer. **Placeholders until set — replace before launch** |
| `VITE_MAP_QUERY` | place on the Contact map and footer; default `Baraton University, Eldoret, Kenya` |
| `VITE_SITE_URL` | live site address (`https://yourdomain.com`); used to generate `sitemap.xml` for Google |
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
- Deploy. Open `https://<backend>.vercel.app/` → the branded **status page** ("Backend running"). `/health/` → `{"status":"ok","service":"rk-ministry-api"}`.
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
- Request bodies ≈ 4.5 MB: the **React admin uploads files straight from the browser to Cloudinary** (the server only signs the
  request, `POST /api/manage/upload-sign/`), so big PDFs/videos work. Limits in the panel: images 10 MB, PDFs 40 MB, videos 100 MB.
  `CLOUDINARY_URL` must be set on the backend for uploads to work.
- Short function timeouts: M-Pesa calls use 8 s timeouts on purpose.
- Admin CSS is served by WhiteNoise with `WHITENOISE_USE_FINDERS=True` (no `collectstatic` step). If `/admin/` ever loads unstyled,
  run `python manage.py collectstatic` locally and commit `staticfiles/` (remove it from `.gitignore`).

## 7. Verification checklist (report pass/fail for each)

Automated
- [ ] `cd backend && python manage.py test` → 43 tests pass
- [ ] `cd frontend && npm run build` → succeeds

Deployed (replace hosts)
- [ ] `https://<backend>/` shows the status page; `curl https://<backend>/health/` → `{"status":"ok",...}`
- [ ] `curl https://<backend>/api/sermons/` → **200**, items have `"locked": true` and **no** `youtube` field; same for `/api/lessons/` (`youtube`,`pdf`), `/api/devotionals/` (`body`), `/api/gallery/` (`link`)
- [ ] `curl -i https://<backend>/api/orders/` → **401**; `curl -i https://<backend>/api/manage/stats/` → **401** (and **403** for a non-staff login)
- [ ] Private window: Home and every page load with no login; the two carousel videos play one after the other
- [ ] Press a sermon / "Watch the lesson" / an article / "View photos" while logged out → the sign-up prompt appears; after login the video or article opens by itself
- [ ] An expired/garbage token in `localStorage.rk_tokens` does not break public pages (the visitor is simply signed out)
- [ ] **Sign up with a real email**: the 6-digit email arrives, wrong code rejected, right code creates the account, welcome popup ~3 s
- [ ] Log in by password, by emailed code, by **Google**; **Forgot password** link works
- [ ] **React admin `/manage`** (as superuser): dashboard loads; create/edit/hide/delete a sermon, lesson, devotional, article, album, product, carousel video; upload a cover (goes to Cloudinary, preview shows); edit the **Pastor biography** and see it on `/about`
- [ ] Like + comment on a sermon → in admin **Comments** (switch *Visible* off hides it on the site)
- [ ] Add to cart → "Added to your cart" pop-up (bottom on phones, top-right on desktop, not covering the WhatsApp bubble); checkout asks visitors to sign up; STK prompt (or simulate) → success → receipt email; order shows **paid** in admin
- [ ] Donation flow completes and shows in admin **Donations**
- [ ] About: pastor photo + biography; Contact: Google map pinned on Baraton University (verify the pin in a real browser) with *Open in Google Maps* and *Get directions*
- [ ] Phone width (≈375 px): drawer slides from the right, cards 2-across, no horizontal scroll (site **and** admin); desktop 3-across
- [ ] Set `VITE_SITE_URL`, redeploy, then `https://<frontend>/sitemap.xml` and `/robots.txt` exist

## 8. API reference (base `/api`, JSON; `Authorization: Bearer <access>` on everything except where noted)

| Method + path | Auth | Purpose |
|---|---|---|
| `POST /auth/register/` `{name,email,password}` | public | validate + email a code → `{pending:true,email}` (no account yet; 30 s resend cooldown → 429) |
| `POST /auth/verify/` `{email,code}` | public | right code → creates account → `{user,access,refresh,created:true}` |
| `POST /auth/login/` `{email,password}` | public | password login |
| `POST /auth/otp/request/` `{email}` | public | email a login code (always 200; never reveals if the email exists) |
| `POST /auth/otp/login/` `{email,code}` | public | login with code |
| `POST /auth/google/` `{credential}` | public | Google ID token → login or create (`created` flag) |
| `POST /auth/refresh/` `{refresh}` | public | new access token |
| `POST /auth/forgot/`, `POST /auth/reset/` | public | password reset (`uid`,`token`,`password`) |
| `GET /auth/me/` | user | current user |
| `GET /hero /sermons /lessons /devotionals /blogs /literature /medical /children /ebooks /gallery /products /about` | **public** | published content. For visitors the protected fields are removed and `"locked": true` is set (see §1) |
| `POST /prayer-requests/`, `POST /contact/` | public | forms; throttled (`FORMS_THROTTLE_RATE`, default 10/hour/IP) + hidden `website` honeypot |
| `GET /engage/<sermon|lesson|devotional>/<id>/` · `POST …/like/` · `POST …/comments/` `{text}` | user | likes + comments |
| `POST /orders/` `{name,email,location,phone,items:[{id,qty}]}` · `GET /orders/<id>/` | user | order + STK push; poll status (`pending|paid|failed`) |
| `POST /donations/` `{amount,phone}` · `GET /donations/<id>/` | user | donation + STK push; poll |
| `POST /mpesa/callback/` | Safaricom | payment result |
| `/manage/stats/`, `/manage/pastor/` (GET/PUT), `/manage/upload-sign/` (POST) | **staff** | dashboard numbers; pastor biography; Cloudinary signature |
| `/manage/{hero,sermons,lessons,devotionals,articles,albums,products}/` CRUD · `/manage/{prayers,messages,comments}/` list/PATCH/DELETE · `/manage/{orders,donations}/` read + `POST <id>/mark-paid/` · `/manage/members/` list/PATCH | **staff** | React admin API. Paginated (20/page), `?q=` search; lists are light (no long text), the edit form loads the full record |

OTP rules (in `accounts/otp.py`): 6 digits, valid 10 min, 5 wrong tries then the code is burned, 30 s resend cooldown,
only a keyed hash is stored, a signup code cannot be used for login.

## 9. Admin cheat-sheet (React panel at `/manage`)

| Section | What you set |
|---|---|
| Carousel videos | upload an MP4 (≤100 MB) or paste a Cloudinary video link, order, shown/hidden. A poster frame is generated automatically |
| Sermons | title, speaker, date, category, **YouTube link** (live thumbnail preview), cover image |
| Sabbath lessons | title, **quarter**, **dates**, teacher, YouTube link, **PDF** upload/link, cover |
| Devotionals | title, **author**, date, scripture, category, summary, text, cover |
| Articles | tabs for Blogs / Literature / Medical / Children / E-books; e-books take a PDF |
| Gallery albums | **mission name**, date, place, **photo album link (https)**, **cover image** (the only thing stored on Cloudinary) |
| Pastor biography | name, title, photo, intro, quote, biography (blank line = new paragraph) |
| Products | name, price (KES), description, image, "available" |
| Orders / Donations | read-only; filter by status; expand a row for items/phone/receipt; **Mark as paid** if Safaricom's callback never arrived |
| Prayer requests / Messages | mark prayed-for / handled; reply by email link |
| Comments | switch **Visible** off to hide; filter by sermon/lesson/devotional |
| Members | switch accounts on/off (never deleted) |

Performance notes: the panel is a separate lazy chunk; lists are paginated with a short in-memory cache; toggles are optimistic;
saves send only the fields that changed; uploads go browser → Cloudinary (photos are resized to ≤1600 px first).
The Django `/admin/` is kept only as a backup (and for granting *Staff* to other people).

## 10. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Browser console: CORS error | `CORS_ALLOWED_ORIGINS` missing the exact frontend origin (scheme+host, no trailing `/`) → fix + redeploy backend |
| `/admin/` (Django backup) login: "CSRF verification failed" | add the backend/custom origin to `CSRF_TRUSTED_ORIGINS` |
| `/manage` says "No access" | the account is not *Staff* (use `createsuperuser`, or tick *Staff* in `/admin/` → Users) and sign in again |
| Admin upload says "Cloudinary is not set up" (503) | `CLOUDINARY_URL` missing on the backend |
| Admin upload fails with "Invalid Signature" | wrong API secret in `CLOUDINARY_URL`, or the server clock is off |
| Someone looks signed in but videos won't open | their saved login expired; the site signs them out automatically on the next load |
| OTP email never arrives | `EMAIL_HOST_USER/PASSWORD` unset (codes only print in logs) or wrong; check spam; Gmail needs an *app password* |
| Sign-up says "We could not send the code email" (502) | SMTP rejected the login/from address → check credentials and `DEFAULT_FROM_EMAIL` |
| Google button shows "not set up yet" | `VITE_GOOGLE_CLIENT_ID` empty at **build** time → set + redeploy frontend |
| Google popup error `origin_mismatch` | frontend origin not in *Authorized JavaScript origins* |
| Google works but API says "Google sign-in failed" | backend `GOOGLE_CLIENT_ID` differs from the frontend's |
| 500s on every API call after deploy | tables not created → run `migrate` against the production `DATABASE_URL` |
| `OperationalError … SSL` locally | local Postgres without SSL → `export DEBUG=1` |
| Orders stay "pending" forever (real M-Pesa) | `MPESA_CALLBACK_URL` wrong/not public, or sandbox shortcode/passkey mismatch |
| Logo broken | the Cloudinary link failed → `/logo.jpg` fallback is automatic; fix `VITE_LOGO_URL` if needed |

## 11. Known limits (be honest with the owner)

- Tested locally: 43 backend tests, a production build, and a headless-browser pass (visitor flow, sign-up gate and resume, cart pop-up,
  albums, About, Contact, and the whole admin panel against a local API with Cloudinary mocked). It has **not** been exercised against
  live Vercel, a real Google client, a real SMTP provider, real Cloudinary uploads or real Daraja — §7 is how you confirm that.
- The Contact map uses Google's key-free embed. Confirm in a real browser that the pin lands on Baraton University; if not, use Google Maps → Share → Embed a map.
- The status page uptime only counts moments when `/health/` or `/` was opened (max once a minute). Point a free uptime monitor
  (e.g. UptimeRobot, every 5 min) at `/health/`.
- Vercel Hobby is for non-commercial use; a store (payments) needs the Pro plan.
- `/api/mpesa/callback/` is unauthenticated (Safaricom does not sign callbacks); it only changes payments whose `CheckoutRequestID` it already knows.
- "Remember me" on the login form is visual only; sessions use JWT (access 12 h, refresh 30 days).
- Content is demo data until the owner replaces it. Contact phone/email are placeholders until `VITE_CONTACT_*` are set.

## 12. Working rules

- Keep tests green; add a test for any backend behaviour you change. Never commit `.env`, `db.sqlite3`, `node_modules`, `dist`.
- Prices are always read from the database on checkout — never trust prices sent by the browser.
- Visitors may list content, but **protected fields must stay removed for anonymous requests** (see `Gated` in `content/serializers.py`). Everything else stays login-only (default permission is `IsAuthenticated`; `/api/manage/*` is staff-only).
- Do not add middleware, global throttles or DRF settings changes: an earlier status feature broke `/api/` that way. The status page is an isolated view.
- Keep field names in `content/serializers.py` in sync with the React components (they are a contract).
