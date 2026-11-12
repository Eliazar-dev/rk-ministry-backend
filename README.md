# Richard Kwanya Snr Ministry — Website

- `frontend/` React (Vite) · `backend/` Django REST API + admin. Both deploy to Vercel.

## Run locally
```bash
# backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate && python manage.py createsuperuser
python manage.py seed_demo            # optional: starter content so the site isn't empty
python manage.py runserver            # http://127.0.0.1:8000  (status page); admin panel: site /manage

# frontend (new terminal)
cd frontend && cp .env.example .env   # set VITE_API_URL=http://127.0.0.1:8000/api
npm install && npm run dev
```
Leave `VITE_API_URL` empty to preview the site with demo data.

## Deploy on Vercel (two projects)
1. **Backend**: import repo, root directory `backend`. Add env vars from `backend/.env.example`
   (needs a Postgres `DATABASE_URL` — Neon, Supabase or Vercel Postgres — plus `SECRET_KEY`, `CLOUDINARY_URL`,
   `CORS_ALLOWED_ORIGINS`). Run `python manage.py migrate` and `createsuperuser` once against that database
   (locally with `DATABASE_URL` exported).
2. **Frontend**: import repo, root directory `frontend`, set `VITE_API_URL=https://<backend>.vercel.app/api`.
3. Put the frontend URL in the backend's `CORS_ALLOWED_ORIGINS`, redeploy the backend.

## Admin panel (React, at `/manage`)
Sign in on the website with a **staff** account (`python manage.py createsuperuser`), then open `/manage` — or tap the gold
dashboard icon in the navbar. Manage carousel videos, sermons, Sabbath lessons, devotionals, articles, gallery albums (cover on
Cloudinary + external photo link), the pastor biography, products, orders, donations, prayer requests, messages, comments and members.
Uploads go straight from the browser to Cloudinary (set `CLOUDINARY_URL` on the backend). Django's `/admin/` remains as a backup.

## Public site, sign-up only on content
Everyone can browse everything. Pressing a video, PDF, article or album link asks for a free account; the API hides those fields from
logged-out requests. Details and the full API table: see **DEVIN.md**.

## M-Pesa and email
- No Daraja keys → **simulate mode**: the STK prompt is faked and auto-confirms after ~25 s (good for demos).
- With `MPESA_*` keys set, a real STK push is sent and Safaricom calls `/api/mpesa/callback/`
  (set `MPESA_CALLBACK_URL` to that public URL).
- Order and donation receipts are emailed when payment is confirmed. Without `EMAIL_HOST_USER` they print to the server log.

## Sign-in
Sign-up is **email OTP** (6-digit code, 10 min, 5 tries); login is password, emailed code, or **Google**.
Set `GOOGLE_CLIENT_ID` (backend) and `VITE_GOOGLE_CLIENT_ID` (frontend). Full setup and deployment steps: see **DEVIN.md**.

## Passwords
"Forgot Password?" emails a reset link to `FRONTEND_URL/reset-password` (set `FRONTEND_URL` on the backend).

## Tests
`cd backend && python manage.py test` — 43 tests: public vs locked fields, OTP signup/login, Google, likes/comments, orders, callbacks, receipt email, password reset, status page, admin API (permissions, CRUD, uploads signing, moderation).
