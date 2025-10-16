#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/root/Meister-Barbershop"

if [ ! -d "${REPO_DIR}/.git" ]; then
  mkdir -p "$(dirname "${REPO_DIR}")"
  git clone "${REPO_URL}" "${REPO_DIR}"
fi

cd "${REPO_DIR}"
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin"

if [ -z "${SECRET_KEY:-}" ]; then
  echo "Missing DJANGO_SECRET_KEY secret. Set secrets.DJANGO_SECRET_KEY in repository settings." >&2
  exit 1
fi

cat <<EOF > backend/.env
SECRET_KEY=${SECRET_KEY}
DJANGO_SECRET_KEY=${SECRET_KEY}
DEBUG=${DEBUG_VALUE:-False}
ALLOWED_HOSTS=${ALLOWED_HOSTS:-localhost,127.0.0.1}
TIME_ZONE=${TIME_ZONE:-Europe/Berlin}
ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-http://localhost:5173}
CSRF_TRUSTED_ORIGINS=${CSRF_TRUSTED_ORIGINS:-http://localhost}
GOOGLE_PLACES_API_KEY=${GOOGLE_PLACES_API_KEY:-}
GOOGLE_PLACE_ID=${GOOGLE_PLACE_ID:-}
EOF

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found. Installing Docker CE..." >&2
  apt-get update
  apt-get install -y ca-certificates curl gnupg lsb-release
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL "https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/gpg" -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/$(. /etc/os-release && echo "$ID") $(lsb_release -cs) stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl enable --now docker
fi

DOCKER_BIN="$(command -v docker)"

if [ -x /usr/bin/docker-compose ]; then
  COMPOSE_CMD="/usr/bin/docker-compose"
elif ${DOCKER_BIN} compose version >/dev/null 2>&1; then
  COMPOSE_CMD="${DOCKER_BIN} compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD="$(command -v docker-compose)"
else
  echo "Docker Compose is not available. Attempting to install plugin..." >&2
  apt-get update
  apt-get install -y docker-compose-plugin
  if ${DOCKER_BIN} compose version >/dev/null 2>&1; then
    COMPOSE_CMD="${DOCKER_BIN} compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="$(command -v docker-compose)"
  else
    echo "Docker Compose installation failed." >&2
    exit 127
  fi
fi

git fetch origin main
git pull origin main

${COMPOSE_CMD} down
${COMPOSE_CMD} build --no-cache
${COMPOSE_CMD} up -d

sleep 15
${COMPOSE_CMD} ps
${DOCKER_BIN} ps

STATUS=$(curl -s -o /tmp/deploy_curl.log -w "%{http_code}" http://localhost || true)
if [ "${STATUS}" -lt 200 ] || [ "${STATUS}" -ge 300 ]; then
  echo "Unexpected HTTP status: ${STATUS}"
  cat /tmp/deploy_curl.log || true
  exit 1
fi

echo "Application responded with HTTP ${STATUS}"

