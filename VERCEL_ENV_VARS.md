# Vercel Environment Variables — Copy & Paste These Exactly

Go to: **Vercel Dashboard → Your Project → Settings → Environment Variables**
Add each variable below one by one. Make sure Environment is set to **Production**.

---

| Variable | Value |
|---|---|
| `SECRET_KEY` | `django-insecure-yi#wzwry7e$=xr6#6)ruf85b6!8g7j38)*h#dhhcid&s2@b3l$` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `dreamhouse-ug.vercel.app,.vercel.app` |
| `DATABASE_URL` | `postgresql://neondb_owner:npg_oXCAmj14RNtu@ep-quiet-water-aq5mgn2m-pooler.c-8.us-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require` |
| `CLOUDINARY_CLOUD_NAME` | `dj7y4rbj6` |
| `CLOUDINARY_API_KEY` | `816875948945751` |
| `CLOUDINARY_API_SECRET` | `UUUeZ0L41TCIBCK4esymBBVIhZA` |
| `EMAIL_HOST_USER` | `frankjames256@gmail.com` |
| `EMAIL_HOST_PASSWORD` | *(your Gmail App Password — see below)* |
| `DEFAULT_FROM_EMAIL` | `frankjames256@gmail.com` |
| `ADMIN_EMAIL` | `mutebifrancis33@gmail.com` |

---

## How to get a Gmail App Password
1. Go to myaccount.google.com
2. Security → Enable 2-Step Verification (must be ON)
3. Security → App Passwords
4. Select "Mail" + "Other" → name it "DreamHouse" → click Generate
5. Copy the 16-character code into `EMAIL_HOST_PASSWORD`

---

## After setting all variables
Vercel auto-redeploys. If it doesn't, go to **Deployments → Redeploy**.

## Run migrations after first deploy
In your terminal (local machine):
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```
Or connect to your Neon DB and ensure tables exist.
