# UltraShop

Multi-tenant online shop platform (Django + Tailwind). See [PRD.md](PRD.md) and [user-stories/](user-stories/) for requirements.

## Phase 0 (current)

- Django project with apps: `core`, `accounts`, `stores`
- Custom user model (email as identifier)
- Store model with unique `username` (subdomain)
- Tenant middleware: resolves `request.store` from host (e.g. `mystore.localhost`, `mystore.ultrashop.local`)
- Signup, login, create store, dashboard

## Run locally

```bash
# Windows (PowerShell)
cd d:\Git\Personal\UltraShop
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

- **Root (platform):** http://127.0.0.1:8000/ — home, login, signup  
- **Create store:** http://127.0.0.1:8000/stores/create/ (after login)  
- **Dashboard:** http://127.0.0.1:8000/dashboard/

### Subdomain in development

To use store subdomains locally:

1. Add to `C:\Windows\System32\drivers\etc\hosts`:
   ```
   127.0.0.1 ultrashop.local
   127.0.0.1 mystore.ultrashop.local
   ```
2. Open http://mystore.ultrashop.local:8000/dashboard/ (replace `mystore` with your store username).

Or use `mystore.localhost` if your system resolves `.localhost` to 127.0.0.1 (e.g. http://mystore.localhost:8000/).

## Environment

Optional: create `.env` and set (or use [.env.example](.env.example) as template):

- `DJANGO_SECRET_KEY` — secret key for production  
- `DJANGO_DEBUG=0` — disable debug  
- `ALLOWED_HOSTS` — comma-separated hosts  
- `PLATFORM_ROOT_DOMAIN` — root domain for subdomain resolution (e.g. `ultrashop.local` or `helpio.ir`)  
- `CSRF_TRUSTED_ORIGINS` — comma-separated full URLs (production only)

## Run with Docker (server)

Build and run on the server (e.g. HELPIO.IR) using only the Dockerfile:

```bash
# Copy env and set production values (see .env.example)
cp .env.example .env
# Edit .env: DJANGO_SECRET_KEY, DJANGO_DEBUG=0, PLATFORM_ROOT_DOMAIN=helpio.ir, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS

# Build image
docker build -t ultrashop .

# Run (volume keeps SQLite + uploads)
docker run -d -p 8000:8000 -e DATA_DIR=/app/data --env-file .env -v ultrashop_data:/app/data --name ultrashop ultrashop

# Create superuser (one-off)
docker exec -it ultrashop gosu appuser python manage.py createsuperuser
```

App listens on port **8000**. Put Nginx/Caddy in front for HTTPS and proxy to `http://127.0.0.1:8000`. Data (SQLite + uploads) is in volume `ultrashop_data`.

### Deployment on HELPIO.IR

1. **DNS:** Point `helpio.ir` and `www.helpio.ir` to your server. For store subdomains (e.g. `mystore.helpio.ir`) add a wildcard A/CNAME: `*.helpio.ir` → your server IP/host.

2. **Environment** (e.g. in `.env` or your process manager):
   ```bash
   DJANGO_SECRET_KEY=<generate-a-secure-key>
   DJANGO_DEBUG=0
   PLATFORM_ROOT_DOMAIN=helpio.ir
   ALLOWED_HOSTS=helpio.ir,.helpio.ir,www.helpio.ir
   CSRF_TRUSTED_ORIGINS=https://helpio.ir,https://www.helpio.ir,https://*.helpio.ir
   ```

3. **Server:** Run Django behind a reverse proxy (Nginx/Caddy) with HTTPS. Serve static files (e.g. `STATIC_ROOT`) and proxy `/` to Django (Gunicorn/uWSGI). Set `SECURE_SSL_REDIRECT` (default True when `DEBUG=0`).

4. **After deploy:** Create a superuser, run migrations, collect static (`python manage.py collectstatic --noinput`). Platform admin: `https://helpio.ir/platform/admin/`.
