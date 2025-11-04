#!/usr/bin/env python3
"""
Telegram notification script for Meister Barbershop monitoring
Sends alerts via the existing telegram-bot container API
"""
import sys
import json
import subprocess
from pathlib import Path

def log(message):
    """Log to stdout and syslog"""
    print(f"[TELEGRAM] {message}", file=sys.stderr)
    subprocess.run(["logger", "-t", "meister-telegram", message], check=False)

def load_secret(env_file="/srv/telegram-bot/.env"):
    """Load TELEGRAM_BOT_SECRET from .env file"""
    try:
        env_path = Path(env_file)
        if not env_path.exists():
            log(f"Warning: {env_file} not found")
            return None

        with open(env_path) as f:
            for line in f:
                if line.startswith("TELEGRAM_BOT_SECRET="):
                    secret = line.split("=", 1)[1].strip().strip('"').strip("'")
                    return secret if secret else None
        return None
    except Exception as e:
        log(f"Error loading secret: {e}")
        return None

def send_notification(message, container_name="telegram-bot"):
    """Send notification via telegram-bot container"""
    try:
        # Load secret
        secret = load_secret()

        # Build payload
        payload = {"text": message}
        if secret:
            payload["secret"] = secret

        # Convert to JSON
        json_payload = json.dumps(payload)

        # Use docker exec with python
        python_cmd = f"""
import json, urllib.request
data = {json_payload!r}.encode('utf-8')
req = urllib.request.Request(
    'http://127.0.0.1:8787/notify',
    data=data,
    headers={{'Content-Type': 'application/json'}}
)
with urllib.request.urlopen(req, timeout=10) as response:
    print(response.read().decode())
"""

        result = subprocess.run(
            ["docker", "exec", container_name, "python", "-c", python_cmd],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0:
            log("✓ Notification sent successfully")
            return True
        else:
            log(f"✗ Failed to send notification: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        log("✗ Timeout sending notification")
        return False
    except Exception as e:
        log(f"✗ Error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        message = "Test notification from Meister monitoring"
    else:
        message = " ".join(sys.argv[1:])

    log("Attempting to send Telegram notification")

    # Check if telegram-bot container exists
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=telegram-bot", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True
        )
        container = result.stdout.strip()

        if not container:
            log("✗ telegram-bot container not found")
            sys.exit(1)

        log(f"Found container: {container}")

    except Exception as e:
        log(f"✗ Error checking container: {e}")
        sys.exit(1)

    # Send notification
    if send_notification(message, container):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
