#!/usr/bin/env bash
set -euo pipefail

LOG_TAG="[meister-backup]"
COMPOSE="docker compose -f /srv/meister/docker-compose.yml"
BACKUP_DIR="/srv/backups/mysql"
TIMESTAMP="$(date +%F_%H%M)"
OUTPUT_FILE="${BACKUP_DIR}/meister_${TIMESTAMP}.sql.gz"

log() {
  local msg="$1"
  printf '%s %s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$LOG_TAG" "$msg"
}

error_trap() {
  local exit_code=$?
  log "ERROR: Backup failed with exit code ${exit_code}." >&2
  exit "$exit_code"
}

trap error_trap ERR

umask 077

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

log "Starting MySQL backup."

DB_ENV=$($COMPOSE exec -T db sh -lc 'printf "%s\n" "$MYSQL_DATABASE|$MYSQL_USER|$MYSQL_PASSWORD"')
IFS='|' read -r DB_NAME DB_USER DB_PASS <<< "$DB_ENV"

if [[ -z "${DB_NAME:-}" || -z "${DB_USER:-}" || -z "${DB_PASS:-}" ]]; then
  log "ERROR: Unable to read database credentials from container environment." >&2
  exit 1
fi

log "Dumping database '${DB_NAME}'."

$COMPOSE exec -T db sh -lc 'MYSQL_PWD="$MYSQL_PASSWORD" mysqldump --single-transaction --routines --triggers --events --skip-lock-tables --no-tablespaces -u"$MYSQL_USER" "$MYSQL_DATABASE"' | gzip -c > "$OUTPUT_FILE"

chmod 600 "$OUTPUT_FILE"

mapfile -t deleted_files < <(find "$BACKUP_DIR" -type f -name '*.sql.gz' -mtime +14 -print -delete)
for old_file in "${deleted_files[@]:-}"; do
  [[ -n "$old_file" ]] && log "Removed old backup: $old_file"
done

FILE_SIZE=$(stat -c%s "$OUTPUT_FILE")
log "Backup complete: $OUTPUT_FILE (${FILE_SIZE} bytes)."

SQL_HEAD=$(zcat "$OUTPUT_FILE" | head -n 5)
log "First lines of dump:"
while IFS= read -r line; do
  log "  $line"
done <<< "$SQL_HEAD"

log "MySQL backup finished successfully."
