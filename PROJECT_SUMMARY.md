# Richard Kwanya Snr Ministry Website

A production-ready ministry website with authentication, protected content, admin panel, store, donations, M-Pesa payments, email OTP, Google sign-in, Cloudinary media, and newsletter system.

**Live Site:** https://www.richardkwanyasnr.org  
**API:** https://api.richardkwanyasnr.org/api  
**Admin Panel:** https://www.richardkwanyasnr.org/manage

---

## Tech Stack

### Frontend
- **React 18** + **Vite**
- **React Router** for navigation
- **Lucide Icons** for UI icons
- **Tailwind CSS** (custom navy/gold theme)
- **Glassmorphism** design system
- **Responsive** mobile-first design

### Backend
- **Django 4.x** + **Django REST Framework**
- **SimpleJWT** for authentication
- **PostgreSQL** database
- **Cloudinary** for media storage
- **Django SMTP** for email
- **Safaricom Daraja API** for M-Pesa payments
- **Africa's Talking** ready for SMS (not yet integrated)

### Deployment
- **Vercel** (separate frontend and backend projects)
- **GitHub** repositories
- **Custom domains** with SSL

---

## Features Implemented

### Authentication & User Management
- ✅ **Email OTP signup** — 6-digit code verification
- ✅ **Password login** (optional)
- ✅ **Google Sign-In** — OAuth 2.0 integration
- ✅ **Password reset** via email
- ✅ **Profile management** — photo upload, password change
- ✅ **Protected routes** — member-only content
- ✅ **JWT tokens** — secure API authentication

### Content Management
- ✅ **Hero Carousel** — video slides with autoplay
- ✅ **Sermons** — YouTube videos with member gating
- ✅ **Sabbath School Lessons** — PDF, video, page images
- ✅ **Devotionals** — daily readings
- ✅ **Articles** — blogs, literature, medical, children, e-books, youth
- ✅ **Mission Gallery** — photo albums
- ✅ **Live Streams** — YouTube live integration
- ✅ **Pastor Biography** — admin-editable profile

### Store & Payments
- ✅ **Product catalog** — admin-managed products
- ✅ **Shopping cart** — session-based cart
- ✅ **Checkout** — M-Pesa STK push integration
- ✅ **Donations** — one-time donation support
- ✅ **Order tracking** — payment status polling
- ✅ **Receipt emails** — automatic confirmation
- ✅ **M-Pesa callback** — Safaricom payment confirmation

### Newsletter System
- ✅ **Footer signup form** — email subscription
- ✅ **Login popup** — prompts unsubscribed users
- ✅ **Auto-email notifications** — new content alerts
- ✅ **Unsubscribe page** — user self-service
- ✅ **Welcome emails** — subscription confirmation

### Admin Panel
- ✅ **Dashboard** — stats and overview
- ✅ **Content CRUD** — all content types editable
- ✅ **User management** — member list and roles
- ✅ **Order/donation tracking** — payment status
- ✅ **Prayer requests** — inbox management
- ✅ **Contact messages** — inbox management
- ✅ **Comments moderation** — approve/hide
- ✅ **Cloudinary uploads** — direct browser uploads
- ✅ **Search & pagination** — efficient data browsing

### SEO & Performance
- ✅ **Meta tags** — dynamic per page
- ✅ **Sitemap** — auto-generated
- ✅ **Robots.txt** — proper crawling rules
- ✅ **Canonical URLs** — duplicate content prevention
- ✅ **Open Graph** — social media sharing
- ✅ **Image optimization** — Cloudinary transformations
- ✅ **Code splitting** — lazy-loaded admin panel
- ✅ **Caching** — API response caching

---

## Project Structure

```
NEW RK MINISTRY/
├── backend/                    # Django REST API
│   ├── accounts/              # Authentication & users
│   ├── content/               # Content models & views
│   ├── shop/                  # Store, orders, M-Pesa
│   ├── newsletter/            # Newsletter subscriptions
│   ├── panel/                 # Admin API endpoints
│   ├── monitoring/            # Health checks
│   ├── config/                # Django settings
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── admin/             # Admin panel (separate chunk)
│   │   ├── api/               # API client & HTTP wrapper
│   │   ├── components/        # Reusable UI components
│   │   ├── context/           # Auth context
│   │   ├── data/              # Mock/demo data
│   │   ├── pages/             # Page components
│   │   ├── styles.css         # Global styles
│   │   └── App.jsx            # Router configuration
│   └── package.json           # Node dependencies
│
└── DEPLOYMENT_STEPS.md        # Deployment guide
```

---

## Environment Variables

### Backend (Vercel)
```bash
# Django
SECRET_KEY=<random-secret-key>
DEBUG=0
ALLOWED_HOSTS=.vercel.app,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://*.vercel.app
DATABASE_URL=<postgresql-connection-string>

# Frontend URL
FRONTEND_URL=https://www.richardkwanyasnr.org
CORS_ALLOWED_ORIGINS=https://www.richardkwanyasnr.org,https://richardkwanya-ministry-frontend.vercel.app

# Email (Gmail SMTP)
EMAIL_HOST_USER=hellorichardkwanyasnr.org@gmail.com
EMAIL_HOST_PASSWORD=<16-char-app-password>
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Richard Kwanya Snr Ministry <no-reply@richardkwanya.org>

# Google Sign-In
GOOGLE_CLIENT_ID=298237414915-ej8j99a5i6an0cboqn48ifbkrcal38hu.apps.googleusercontent.com

# Cloudinary
CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>

# M-Pesa (Production)
MPESA_ENV=production
MPESA_CONSUMER_KEY=<consumer-key>
MPESA_CONSUMER_SECRET=<consumer-secret>
MPESA_PASSKEY=<passkey>
MPESA_SHORTCODE=1206783
MPESA_TILL_NUMBER=1678528
MPESA_TRANSACTION_TYPE=CustomerBuyGoodsOnline
MPESA_CALLBACK_URL=https://api.richardkwanyasnr.org/api/mpesa/callback/
```

### Frontend (Vercel)
```bash
VITE_API_URL=https://api.richardkwanyasnr.org/api
VITE_GOOGLE_CLIENT_ID=298237414915-ej8j99a5i6an0cboqn48ifbkrcal38hu.apps.googleusercontent.com
VITE_SITE_URL=https://www.richardkwanyasnr.org
VITE_WHATSAPP_NUMBER=254743346573
VITE_CONTACT_PHONE=+254 743 346 573
VITE_CONTACT_EMAIL=info@richardkwanya.org
VITE_MAP_QUERY=Baraton University, Eldoret, Kenya
```

---

## API Endpoints

### Public API
- `GET /api/hero/` — Carousel slides
- `GET /api/sermons/` — Sermon list
- `GET /api/lessons/` — Sabbath School lessons
- `GET /api/devotionals/` — Daily devotionals
- `GET /api/articles/` — Articles (blogs, literature, etc.)
- `GET /api/albums/` — Mission gallery albums
- `GET /api/products/` — Store products
- `GET /api/about/` — Pastor profile
- `GET /api/live/` — Live stream info
- `GET /api/youth/` — Youth ministries content

### Authentication
- `POST /api/auth/signup/` — Email OTP signup
- `POST /api/auth/login/` — Password or OTP login
- `POST /api/auth/google/` — Google sign-in
- `POST /api/auth/refresh/` — Refresh JWT token
- `GET /api/auth/me/` — Current user info
- `POST /api/auth/password/` — Set/change password
- `POST /api/auth/forgot-password/` — Password reset request
- `POST /api/auth/reset-password/` — Password reset confirm

### Payments
- `POST /api/orders/` — Create store order (M-Pesa STK)
- `GET /api/orders/<id>/` — Order status
- `POST /api/donations/` — Create donation (M-Pesa STK)
- `GET /api/donations/<id>/` — Donation status
- `POST /api/mpesa/callback/` — Safaricom payment callback

### Newsletter
- `POST /api/newsletter/subscribe/` — Subscribe to newsletter
- `POST /api/newsletter/unsubscribe/` — Unsubscribe
- `GET /api/newsletter/me/` — Check subscription status (auth required)
- `GET /api/newsletter/subscribers/` — List subscribers (staff only)

### Admin API (`/api/manage/`)
- `GET /api/manage/stats/` — Dashboard statistics
- `GET/POST/PATCH/DELETE /api/manage/hero/` — Carousel management
- `GET/POST/PATCH/DELETE /api/manage/sermons/` — Sermon management
- `GET/POST/PATCH/DELETE /api/manage/lessons/` — Lesson management
- `GET/POST/PATCH/DELETE /api/manage/devotionals/` — Devotional management
- `GET/POST/PATCH/DELETE /api/manage/articles/` — Article management
- `GET/POST/PATCH/DELETE /api/manage/albums/` — Gallery management
- `GET/POST/PATCH/DELETE /api/manage/products/` — Product management
- `GET/PATCH/DELETE /api/manage/prayers/` — Prayer requests
- `GET/PATCH/DELETE /api/manage/messages/` — Contact messages
- `GET/PATCH/DELETE /api/manage/comments/` — Comment moderation
- `GET/PATCH /api/manage/members/` — Member management
- `GET /api/manage/pastor/` — Pastor profile
- `POST /api/manage/upload-sign/` — Cloudinary upload signature

---

## Database Models

### Accounts
- **User** — Custom user model with email auth
- **OTPCode** — Email verification codes
- **PasswordReset** — Password reset tokens

### Content
- **HeroSlide** — Carousel videos
- **Sermon** — YouTube sermon videos
- **Lesson** — Sabbath School lessons
- **LessonPage** — Lesson page images
- **Devotional** — Daily devotionals
- **Article** — Blog/literature/medical/children/ebook/youth articles
- **Album** — Mission gallery albums
- **LiveStream** — Live stream configuration
- **PastorProfile** — Pastor biography
- **Comment** — User comments on content
- **PrayerRequest** — Prayer request submissions
- **ContactMessage** — Contact form messages

### Shop
- **Product** — Store products
- **Order** — Customer orders
- **OrderItem** — Order line items
- **Donation** — Donation records
- **Payment** — Payment tracking (base model)

### Newsletter
- **NewsletterSubscriber** — Email subscribers

---

## Key Features Detail

### M-Pesa Integration
- **STK Push** — Customer receives prompt on phone
- **Buy Goods/Till** — Uses `CustomerBuyGoodsOnline` transaction type
- **BusinessShortCode vs PartyB** — `1206783` (approval) vs `1678528` (till)
- **Callback handling** — Safaricom sends payment confirmation
- **Receipt emails** — Automatic after successful payment
- **Order tracking** — Real-time status polling

### Email System
- **SMTP** — Gmail SMTP with app password
- **OTP codes** — 6-digit verification codes
- **Password reset** — Secure reset links
- **Newsletter notifications** — New content alerts
- **Receipt emails** — Payment confirmations
- **Welcome emails** — Subscription confirmations

### Cloudinary Integration
- **Direct uploads** — Browser uploads straight to Cloudinary
- **Image optimization** — Automatic resizing and format conversion
- **Video hosting** — Cloudinary video URLs
- **PDF storage** — Raw file uploads for lessons/e-books
- **Folder organization** — `rk/covers`, `rk/pdfs`, `rk/videos`, etc.

### Security
- **JWT authentication** — Secure token-based auth
- **Password hashing** — Django's default PBKDF2
- **CORS protection** — Whitelisted origins only
- **CSRF protection** — Django CSRF middleware
- **Rate limiting** — OTP resend cooldown
- **Input validation** — All user inputs validated
- **SQL injection protection** — Django ORM
- **XSS protection** — React's built-in escaping

---

## Testing

### Backend Tests
```bash
cd backend
python manage.py test
```

### Frontend Build
```bash
cd frontend
npm run build
```

### Manual Testing
1. **Authentication** — Signup, login, Google sign-in, password reset
2. **Content** — View sermons, lessons, devotionals, articles
3. **Store** — Add to cart, checkout, M-Pesa payment
4. **Donations** — Make donation, receive confirmation
5. **Newsletter** — Subscribe, receive welcome email
6. **Admin** — Login, create/edit content, view stats

---

## Deployment

### Vercel Setup
1. **Backend project** — Connect to `rk-ministry-backend` GitHub repo
2. **Frontend project** — Connect to `rk-ministry--Frontend` GitHub repo
3. **Environment variables** — Set all required vars in Vercel
4. **Domains** — Configure custom domains
5. **Auto-deploy** — Pushes to master trigger deployments

### Database
- **PostgreSQL** — Hosted on Vercel Postgres or external provider
- **Migrations** — Run automatically on deployment
- **Backup** — Regular database backups recommended

### Monitoring
- **Health endpoint** — `GET /health/` for uptime checks
- **Status page** — `GET /` shows system status
- **Error logging** — Django logs to Vercel

---

## Support & Maintenance

### Admin Access
- **URL:** https://www.richardkwanyasnr.org/manage
- **Login:** Use staff account credentials
- **Features:** Content management, user management, order tracking

### Content Updates
- **Sermons** — Upload via admin panel
- **Lessons** — Upload PDF/pages via admin panel
- **Articles** — Create/edit via admin panel
- **Products** — Add/edit store items via admin panel
- **Gallery** — Add mission albums via admin panel

### Troubleshooting
- **Login issues** — Check email OTP, password reset
- **Payment issues** — Check M-Pesa credentials, callback URL
- **Email issues** — Check SMTP settings, app password
- **Upload issues** — Check Cloudinary credentials, file size limits
- **Admin access** — Verify staff permissions, JWT tokens

---

## Future Enhancements

### Planned Features
- **SMS notifications** — Africa's Talking integration for OTP/alerts
- **Push notifications** — Browser push for new content
- **Mobile app** — React Native or Flutter app
- **Multi-language** — Swahili/English support
- **Advanced analytics** — Google Analytics, custom dashboards
- **E-commerce** — Payment gateway alternatives (card, bank)
- **Membership tiers** — Premium content subscriptions
- **Live chat** — Customer support integration
- **Calendar** — Event scheduling and reminders

### Technical Improvements
- **Caching** — Redis for session/data caching
- **CDN** — CloudFront for static assets
- **Monitoring** — Sentry for error tracking
- **CI/CD** — GitHub Actions for automated testing
- **Database** — Read replicas for performance
- **API versioning** — Versioned API endpoints

---

## Credits & Acknowledgments

**Developed by:** TECHIVE IT SOLUTIONS  
**Client:** Richard Kwanya Snr Ministry  
**Ministry Motto:** "Equipping people, transforming lives. Impacting Generations for Christ"

**Technologies Used:**
- React, Django, PostgreSQL, Vercel, Cloudinary, Safaricom Daraja, Gmail SMTP, Google OAuth

**Design:** Navy/gold glassmorphism theme with responsive layout

---

## License

This project is proprietary software developed for Richard Kwanya Snr Ministry. All rights reserved.

---

## Contact

**Website:** https://www.richardkwanyasnr.org  
**Email:** info@richardkwanya.org  
**WhatsApp:** +254 743 346 573  
**Admin:** https://www.richardkwanyasnr.org/manage

---

*Project completed and deployed successfully. All systems operational.*
