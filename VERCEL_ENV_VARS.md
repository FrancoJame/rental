# Vercel Environment Variables — Required Setup

Go to: Vercel Dashboard → Your Project → Settings → Environment Variables

Add ALL of the following variables:

| Variable | Value |
|---|---|
| `SECRET_KEY` | `django-insecure-yi#wzwry7e$=xr6#6)ruf85b6!8g7j38)*h#dhhcid&s2@b3l$` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `dreamhouse-ug.vercel.app,.vercel.app` |
| `DATABASE_URL` | Your Neon/Supabase PostgreSQL URL |
| `CLOUDINARY_CLOUD_NAME` | `dj7y4rbj6` |
| `CLOUDINARY_API_KEY` | `816875948945751` |
| `CLOUDINARY_API_SECRET` | `UUUeZ0L41TCIBCK4esymBBVIhZA` |
| `EMAIL_HOST_USER` | `frankjames256@gmail.com` |
| `EMAIL_HOST_PASSWORD` | Your Gmail App Password (see below) |
| `DEFAULT_FROM_EMAIL` | `frankjames256@gmail.com` |
| `ADMIN_EMAIL` | `mutebifrancis33@gmail.com` |

---

## CRITICAL: Why the site shows 500 on startup

If you deployed without these env vars, the app crashes immediately because:
1. `CLOUDINARY_CLOUD_NAME` missing → cloudinary_storage fails to initialise
2. `DATABASE_URL` missing → falls back to SQLite (read-only on Vercel, crashes on write)
3. `SECRET_KEY` missing → Django refuses to start

**Every variable above must be set in Vercel before the site works.**

---

## How to get a Gmail App Password (NOT your real password)
1. Go to myaccount.google.com
2. Security → Enable 2-Step Verification if not already on
3. Security → App Passwords
4. Select "Mail" + "Other (custom)" → name it "DreamHouse"
5. Copy the 16-character code → paste as `EMAIL_HOST_PASSWORD`

---

## After adding env vars
Vercel will redeploy automatically. If not, go to Deployments → Redeploy.
