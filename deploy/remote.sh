#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/srv/meister}"
REPO_URL="${REPO_URL:?REPO_URL is required}"

if command -v sudo >/dev/null 2>&1 && [ "$(id -u)" -ne 0 ]; then
  SUDO_CMD="sudo"
else
  SUDO_CMD=""
fi

run_with_sudo() {
  if [ -n "${SUDO_CMD}" ]; then
    "${SUDO_CMD}" "$@"
  else
    "$@"
  fi
}

run_with_sudo mkdir -p "${APP_DIR}"
if [ -n "${SUDO_CMD}" ]; then
  run_with_sudo chown "$(id -u):$(id -g)" "${APP_DIR}"
fi

if [ ! -d "${APP_DIR}/.git" ]; then
  git clone "${REPO_URL}" "${APP_DIR}"
fi

cd "${APP_DIR}"

if [ ! -f "backend/.env" ]; then
  for legacy_dir in /root/Meister-Barbershop /srv/Meister-Barbershop; do
    if [ -f "${legacy_dir}/backend/.env" ]; then
      echo "Reusing existing backend environment file from ${legacy_dir}" >&2
      run_with_sudo cp "${legacy_dir}/backend/.env" "backend/.env"
      if [ -n "${SUDO_CMD}" ]; then
        run_with_sudo chown "$(id -u):$(id -g)" "backend/.env"
      fi
      break
    fi
  done
fi

if [ ! -f "backend/.env" ]; then
  echo "Missing backend/.env on the server. Create it once with the required secrets and rerun the deploy." >&2
  exit 1
fi

git fetch origin main
git reset --hard origin/main

if ! command -v docker >/dev/null 2>&1; then
  run_with_sudo apt-get update
  run_with_sudo apt-get install -y ca-certificates curl gnupg lsb-release
  run_with_sudo install -m 0755 -d /etc/apt/keyrings
  run_with_sudo curl -fsSL "https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/gpg" -o /etc/apt/keyrings/docker.asc
  run_with_sudo chmod a+r /etc/apt/keyrings/docker.asc
  ARCH="$(dpkg --print-architecture)"
  DIST_ID="$(. /etc/os-release && echo "$ID")"
  DIST_CODENAME="$(lsb_release -cs)"
  if [ -n "${SUDO_CMD}" ]; then
    printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/%s %s stable\n' "${ARCH}" "${DIST_ID}" "${DIST_CODENAME}" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  else
    printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/%s %s stable\n' "${ARCH}" "${DIST_ID}" "${DIST_CODENAME}" | tee /etc/apt/sources.list.d/docker.list > /dev/null
  fi
  run_with_sudo apt-get update
  run_with_sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  run_with_sudo systemctl enable --now docker
fi

if ! command -v curl >/dev/null 2>&1; then
  run_with_sudo apt-get update
  run_with_sudo apt-get install -y curl
fi

DOCKER_BIN="$(command -v docker)"

compose() {
  "${DOCKER_BIN}" compose "$@"
}

if ${DOCKER_BIN} compose version >/dev/null 2>&1; then
  :
elif command -v docker-compose >/dev/null 2>&1; then
  compose() {
    docker-compose "$@"
  }
else
  run_with_sudo apt-get update
  run_with_sudo apt-get install -y docker-compose-plugin
  if ${DOCKER_BIN} compose version >/dev/null 2>&1; then
    :
  elif command -v docker-compose >/dev/null 2>&1; then
    compose() {
      docker-compose "$@"
    }
  else
    echo "Docker Compose is not available." >&2
    exit 127
  fi
fi

for legacy_dir in /root/Meister-Barbershop /srv/Meister-Barbershop; do
  if [ "${legacy_dir}" = "${APP_DIR}" ]; then
    continue
  fi
  if [ -f "${legacy_dir}/docker-compose.yml" ]; then
    (
      cd "${legacy_dir}"
      echo "Stopping legacy stack in ${legacy_dir}" >&2
      if ${DOCKER_BIN} compose version >/dev/null 2>&1; then
        ${DOCKER_BIN} compose down || true
      elif command -v docker-compose >/dev/null 2>&1; then
        docker-compose down || true
      fi
    )
  fi
done

compose down || true
compose build --no-cache
compose up -d

compose ps

HEALTH_URL="${HEALTH_URL:-http://localhost}"
STATUS=""
for attempt in $(seq 1 12); do
  STATUS=$(curl -s -o /tmp/deploy_health.log -w "%{http_code}" "${HEALTH_URL}" || true)
  if [ "${STATUS}" -ge 200 ] && [ "${STATUS}" -lt 300 ]; then
    break
  fi
  sleep 5
done

if [ "${STATUS}" -lt 200 ] || [ "${STATUS}" -ge 300 ]; then
  echo "Unexpected HTTP status after retries: ${STATUS}"
  cat /tmp/deploy_health.log || true
  exit 1
fi

echo "Application responded with HTTP ${STATUS}"
