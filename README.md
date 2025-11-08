# Meister Barbershop

Monorepo with Django REST backend and React (Vite) frontend.

## Structure
- `backend/` – Django REST API
- `frontend/` – React single page app
- `deploy/` – Container / proxy configuration
- `.github/workflows/` – Continuous integration and delivery

## Local Development
- **Backend**  
  ```bash
  cd backend
  python -m venv .venv
  .venv/bin/pip install -r requirements.txt
  cp .env.sample .env  # adjust for your machine
  .venv/bin/python manage.py migrate
  .venv/bin/python manage.py runserver
  ```
- **Frontend**  
  ```bash
  cd frontend
  cp .env.sample .env  # adjust VITE_API_BASE if needed
  npm install
  npm run dev
  ```

## Dockerized Deployment
Three services are defined in `docker-compose.yml`:
- `backend`: Django + Gunicorn (`ghcr.io/al1mk/meister-backend`)
- `frontend`: Vite build served by Nginx (`ghcr.io/al1mk/meister-frontend`)
- `reverse-proxy`: Nginx edge proxy routing `/` → frontend, `/api/` and `/media/` → backend

The compose stack mounts a named volume (`media_data`) so uploads persist across restarts. Health checks are baked into each container.

### Building locally
```bash
docker compose build
docker compose up -d
```
Visit `http://localhost` for the SPA and `http://localhost/api/` for the API.

## Environment Files
- `backend/.env.sample` – Django configuration (secret key, DB, CORS, Google keys). Copy to `.env` before running locally or deploying.
- `frontend/.env.sample` – Frontend build-time settings. `VITE_API_BASE=/api` keeps the SPA on the same origin as the API in production.

## One-time Server Bootstrap (Ubuntu)
1. Install Docker + Compose:
   ```bash
   sudo apt-get update
   sudo apt-get install -y ca-certificates curl gnupg
   sudo install -m 0755 -d /etc/apt/keyrings
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   sudo apt-get update
   sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   ```
2. Log in to GHCR (requires GitHub PAT with `write:packages`):
   ```bash
   echo "${GHCR_TOKEN}" | sudo docker login ghcr.io -u "${GHCR_USERNAME}" --password-stdin
   ```
3. Prepare runtime directory:
   ```bash
   sudo mkdir -p /srv/meister
   sudo chown $USER:$USER /srv/meister
   ```
4. Copy `docker-compose.yml` plus `backend/.env` and (optionally) `frontend/.env` into `/srv/meister`.
5. Launch services:
   ```bash
   cd /srv/meister
   docker compose pull
   docker compose up -d
   ```

The reverse proxy listens on port 80, serves the built frontend at `/`, and proxies `/api/` and `/media/` to the backend (Gunicorn on port 8000). When HTTPS certificates become available, enable them by extending the proxy config in `deploy/reverse-proxy/nginx.conf`.

## Continuous Integration & Delivery
The GitHub Actions workflow (`.github/workflows/deploy.yml`) runs quality gates, builds both images, publishes them to GHCR with tags `latest` and the Git SHA, and can optionally redeploy via SSH on push to `main`. Configure required secrets in the repository settings (see workflow file for details).
# Force rebuild graph 2025-11-08T19:09:38Z
