# Meister Barbershop

A modern, full-stack booking platform for barbershop appointments. This application streamlines the entire customer journey from browsing available barbers to booking appointments, with real-time notifications and multi-language support.

## Overview

Meister Barbershop is built as a monorepo containing a Django REST backend and a React frontend, designed for easy deployment with Docker. The platform handles appointment scheduling, customer communications, and administrative tasks with a clean, responsive interface.

## Features

- **Online Booking System** – Customers can view available time slots and book appointments with their preferred barber
- **Multi-Language Support** – Full German and English translations using i18next
- **Smart Notifications** – Automated SMS and email confirmations for bookings using Twilio and Mailgun/SendGrid
- **Admin Dashboard** – Manage schedules, view bookings, and handle customer requests
- **Barber Profiles** – Showcase team members with photos and specialties
- **Customer Reviews** – Collect and display feedback from satisfied customers
- **Contact Form** – Direct communication channel with automated email routing
- **Responsive Design** – Works seamlessly on desktop, tablet, and mobile devices
- **Real-time Updates** – Webhook support for instant booking confirmations
- **Error Monitoring** – Integrated Sentry for tracking and resolving issues quickly

## Tech Stack

### Frontend
- **React 18** with Vite for fast development and optimized builds
- **React Router** for seamless navigation
- **i18next** for internationalization (German/English)
- **Tailwind CSS** with custom UI components
- **React Day Picker** for intuitive date selection
- **Nginx** for production serving

### Backend
- **Django 5.2** with Django REST Framework
- **MySQL** database for reliable data storage
- **Gunicorn** WSGI server with multiple workers
- **Twilio** for SMS notifications
- **Django-Anymail** with Mailgun/SendGrid integration
- **drf-spectacular** for API documentation
- **Python 3.12**

### Infrastructure
- **Docker & Docker Compose** for containerized multi-service deployment
- **Nginx** reverse proxy with health checks and timeout configurations
- **HTTPS** via Cloudflare
- **GitHub Actions** for CI/CD pipeline
- **Systemd** services for monitoring and auto-recovery
- **Automated backups** and log rotation

## Project Structure

```
meister-barbershop/
├── backend/              # Django REST API
│   ├── barbers/         # Barber profiles and management
│   ├── bookings/        # Appointment scheduling and notifications
│   ├── contact/         # Contact form handling
│   ├── reviews/         # Customer reviews
│   └── config/          # Django settings and configuration
├── frontend/            # React single-page application
│   └── src/
│       ├── components/  # Reusable UI components
│       ├── pages/       # Main application pages
│       ├── sections/    # Page sections
│       ├── i18n/        # Translation files
│       └── hooks/       # Custom React hooks
├── deploy/              # Docker and proxy configurations
│   ├── backend/         # Backend container setup
│   ├── frontend/        # Frontend container setup
│   └── reverse-proxy/   # Nginx proxy configuration
└── .github/workflows/   # CI/CD automation
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ and npm (for local frontend development)
- Python 3.12+ (for local backend development)
- MySQL 8.0+ (for local backend development)

### Local Development

**Backend Setup**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.sample .env        # Configure your environment variables
python manage.py migrate
python manage.py runserver
```

The backend API will be available at `http://localhost:8000/api/`

**Frontend Setup**
```bash
cd frontend
npm install
cp .env.sample .env        # Adjust VITE_API_BASE if needed
npm run dev
```

The frontend will be available at `http://localhost:5173/`

### Docker Deployment

The application is designed to run as three interconnected services:
- `backend` – Django + Gunicorn (`ghcr.io/al1mk/meister-backend`)
- `frontend` – Vite build served by Nginx (`ghcr.io/al1mk/meister-frontend`)
- `reverse-proxy` – Nginx routing `/` to frontend, `/api/` and `/media/` to backend

**Build and run locally:**
```bash
docker compose build
docker compose up -d
```

Visit `http://localhost` to access the application.

**View logs:**
```bash
docker compose logs -f
```

**Stop services:**
```bash
docker compose down
```

## Environment Configuration

### Backend Environment Variables
Copy `backend/.env.sample` to `backend/.env` and configure:

```env
# Django Core
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com

# Database
DB_NAME=meister_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306

# CORS (for local development)
CORS_ALLOWED_ORIGINS=http://localhost:5173

# Email
MAILGUN_API_KEY=your-mailgun-key
MAILGUN_SENDER_DOMAIN=mg.yourdomain.com

# SMS
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890

# Error Monitoring
SENTRY_DSN=your-sentry-dsn
```

### Frontend Environment Variables
Copy `frontend/.env.sample` to `frontend/.env`:

```env
# API endpoint (use /api for same-origin in production)
VITE_API_BASE=/api

# Error Monitoring
VITE_SENTRY_DSN=your-sentry-dsn
```

## Production Deployment

### Server Setup (Ubuntu)

1. **Install Docker and Docker Compose:**
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

2. **Authenticate with GitHub Container Registry:**
```bash
echo "${GHCR_TOKEN}" | sudo docker login ghcr.io -u "${GHCR_USERNAME}" --password-stdin
```

3. **Prepare deployment directory:**
```bash
sudo mkdir -p /srv/meister
sudo chown $USER:$USER /srv/meister
```

4. **Deploy configuration files:**
   - Copy `docker-compose.yml` to `/srv/meister/`
   - Copy `backend/.env` (with production values) to `/srv/meister/backend/.env`
   - Optionally copy `frontend/.env` to `/srv/meister/frontend/.env`

5. **Launch the application:**
```bash
cd /srv/meister
docker compose pull
docker compose up -d
```

The reverse proxy listens on port 80 and routes traffic appropriately. For HTTPS support, configure SSL certificates in `deploy/reverse-proxy/nginx.conf`.

### Continuous Integration & Delivery

The GitHub Actions workflow at `.github/workflows/deploy.yml` automates:
- Code linting and quality checks
- Docker image building for both backend and frontend
- Publishing images to GitHub Container Registry with `latest` and Git SHA tags
- Optional SSH deployment to production on push to `main` branch

**Required GitHub Secrets:**
- `GHCR_TOKEN` – GitHub Personal Access Token with `write:packages` permission
- `SSH_HOST` – Production server IP or domain
- `SSH_USERNAME` – SSH user for deployment
- `SSH_PRIVATE_KEY` – Private key for SSH authentication
- `SSH_PORT` – SSH port (default: 22)

## API Documentation

Once the backend is running, interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`
- ReDoc: `http://localhost:8000/api/schema/redoc/`

## Health Checks

The application includes health check endpoints and automated monitoring:
- Backend health: `http://localhost:8000/api/health/`
- Systemd services monitor container health and restart on failures
- Nginx configured with appropriate timeouts to prevent 502/504 errors

## Development Workflow

1. **Make changes** in your local environment
2. **Test locally** using Docker Compose or development servers
3. **Commit changes** following conventional commit format
4. **Push to GitHub** – CI/CD pipeline runs automatically
5. **Deploy to production** – Either manually via SSH or automatically on merge to `main`

## Troubleshooting

**Backend container won't start:**
- Check environment variables in `backend/.env`
- Verify database credentials and connection
- Review logs: `docker compose logs backend`

**Frontend shows API errors:**
- Verify `VITE_API_BASE` is set correctly
- Check CORS settings in backend `.env`
- Ensure backend is running and accessible

**502 Bad Gateway errors:**
- Check backend container health: `docker compose ps`
- Verify Gunicorn workers are running: `docker compose logs backend`
- Review nginx configuration in `deploy/reverse-proxy/nginx.conf`

## Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes with clear, descriptive messages
4. Push to your branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is private and proprietary. All rights reserved.

---

Built with care for Meister Barbershop | [Website](https://www.meisterbarbershop.de)
