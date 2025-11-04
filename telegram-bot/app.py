"""
Telegram Bot Service
- FastAPI endpoint POST /notify for receiving booking events from Django
- Telegram bot polling worker for handling group commands (/today, /tomorrow, /stats, /help)
"""
import os
import logging
import asyncio
from threading import Thread
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import uvicorn
import httpx
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment
env_path = Path("/app/.env")
if not env_path.exists():
    raise SystemExit("Missing /app/.env")
load_dotenv(env_path)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_GROUP_ID = os.getenv("TELEGRAM_GROUP_ID")
TELEGRAM_BOT_SECRET = os.getenv("TELEGRAM_BOT_SECRET", "")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000/api/appointments")
PUBLIC_API_BASE = os.getenv("PUBLIC_API_BASE", "https://www.meisterbarbershop.de")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_GROUP_ID:
    raise SystemExit("TELEGRAM_BOT_TOKEN and TELEGRAM_GROUP_ID must be set")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Telegram Notify", docs_url=None, redoc_url=None)

class NotifyPayload(BaseModel):
    text: str | None = None
    appointment: dict | None = None
    event: str | None = None
    secret: str | None = None

def escape_markdown(text: str) -> str:
    """Escape special characters for Markdown"""
    # Escape Markdown special characters
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

@app.get("/healthz")
async def healthz():
    return {"ok": True}

async def send_telegram_message(text: str, parse_mode: str = "Markdown"):
    """Send message to Telegram group"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = await client.post(url, json={
            "chat_id": TELEGRAM_GROUP_ID,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        })
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Telegram API error: {resp.text}")
    return resp.json()

@app.post("/notify")
async def notify(payload: NotifyPayload, request: Request):
    """Receive booking notifications from Django backend"""
    # IP check - allow Docker network
    client_host = request.client.host
    if not (client_host == "127.0.0.1" or client_host == "localhost" or client_host.startswith("172.")):
        raise HTTPException(status_code=403, detail="Forbidden")

    # Secret verification
    if TELEGRAM_BOT_SECRET:
        if not payload.secret or payload.secret != TELEGRAM_BOT_SECRET:
            raise HTTPException(status_code=401, detail="Invalid secret")

    # Build message
    if payload.text:
        text = payload.text
    elif payload.appointment:
        appt = payload.appointment
        event = payload.event or "unknown"

        # Helper to escape markdown
        def esc(s):
            return escape_markdown(str(s))

        # Format notification based on event type
        if event == "created":
            text = "💈 *New Appointment Confirmed!*\n\n"
            text += f"👤 Customer: {esc(appt.get('customer', 'N/A'))}\n"
            text += f"💇‍♂️ Barber: {esc(appt.get('barber', 'N/A'))}\n"
            text += f"🕒 Time: {esc(appt.get('time', 'N/A'))}\n"
            text += f"✂️ Service: {esc(appt.get('service', 'N/A'))}\n"
            if appt.get('notes'):
                text += f"📝 Notes: {esc(appt.get('notes'))}\n"
            text += f"\n_ID: {esc(appt.get('id', 'N/A'))}_"

        elif event == "updated":
            text = "✏️ *Appointment Updated*\n\n"
            text += f"👤 Customer: {esc(appt.get('customer', 'N/A'))}\n"
            text += f"💇‍♂️ Barber: {esc(appt.get('barber', 'N/A'))}\n"
            text += f"🕒 New time: {esc(appt.get('time', 'N/A'))}\n"
            text += f"✂️ Service: {esc(appt.get('service', 'N/A'))}\n"
            if appt.get('notes'):
                text += f"📝 Notes: {esc(appt.get('notes'))}\n"
            text += f"\n_ID: {esc(appt.get('id', 'N/A'))}_"

        elif event == "deleted":
            text = "🗑 *Appointment Cancelled*\n\n"
            text += f"👤 Customer: {esc(appt.get('customer', 'N/A'))}\n"
            text += f"💇‍♂️ Barber: {esc(appt.get('barber', 'N/A'))}\n"
            text += f"🕒 Time: {esc(appt.get('time', 'N/A'))}\n"
            text += f"✂️ Service: {esc(appt.get('service', 'N/A'))}\n"
            text += f"\n_ID: {esc(appt.get('id', 'N/A'))}_"

        else:
            text = f"📌 *Appointment {event}*\n\n"
            text += f"Customer: {esc(appt.get('customer', 'N/A'))}\n"
            text += f"Barber: {esc(appt.get('barber', 'N/A'))}\n"
            text += f"Time: {esc(appt.get('time', 'N/A'))}\n"
            text += f"Service: {esc(appt.get('service', 'N/A'))}\n"
            if appt.get('notes'):
                text += f"Notes: {esc(appt.get('notes'))}\n"
            text += f"ID: {esc(appt.get('id', 'N/A'))}"
    else:
        raise HTTPException(status_code=400, detail="No text or appointment provided")

    # Send to Telegram
    result = await send_telegram_message(text)
    logger.info(f"Notification sent: {event if payload.appointment else 'text'}")
    return {"ok": True, "result": result}

# Telegram Bot Commands
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_text = (
        "📋 *Meister Barbershop Bot*\n\n"
        "Available commands:\n"
        "💬 /help — _Show this help message_\n"
        "📅 /today — _Show today's appointments_\n"
        "🗓 /tomorrow — _Show tomorrow's appointments_\n"
        "📊 /stats — _Show today's statistics_\n"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and show today's appointments"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"{PUBLIC_API_BASE}/api/appointments/today/"
            resp = await client.get(url)
            resp.raise_for_status()
            appointments = resp.json()

        if not appointments:
            text = "📅 *Today's Appointments*\n\n😴 No appointments scheduled\\."
            await update.message.reply_text(text, parse_mode='Markdown')
            return

        text = f"📅 *Today's Appointments* \\({len(appointments)}\\)\n\n"
        for i, appt in enumerate(appointments, 1):
            customer = escape_markdown(appt.get('customer', '?'))
            barber = escape_markdown(appt.get('barber', '?'))
            service = escape_markdown(appt.get('service', '?'))
            time = escape_markdown(appt.get('time', '?'))

            text += f"*{i}\\. {time}*\n"
            text += f"👤 {customer}\n"
            text += f"💇‍♂️ Barber: {barber}\n"
            text += f"✂️ Service: {service}\n\n"

        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            error_msg = f"Status {e.response.status_code}: {e.response.text[:200]}"
        logger.error(f"Error fetching today's appointments: {error_msg}")
        await update.message.reply_text(f"❌ Error fetching appointments: {escape_markdown(error_msg)}", parse_mode='Markdown')

async def tomorrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and show tomorrow's appointments"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"{PUBLIC_API_BASE}/api/appointments/tomorrow/"
            resp = await client.get(url)
            resp.raise_for_status()
            appointments = resp.json()

        if not appointments:
            text = "🗓 *Tomorrow's Appointments*\n\n😴 No appointments scheduled\\."
            await update.message.reply_text(text, parse_mode='Markdown')
            return

        text = f"🗓 *Tomorrow's Appointments* \\({len(appointments)}\\)\n\n"
        for i, appt in enumerate(appointments, 1):
            customer = escape_markdown(appt.get('customer', '?'))
            barber = escape_markdown(appt.get('barber', '?'))
            service = escape_markdown(appt.get('service', '?'))
            time = escape_markdown(appt.get('time', '?'))

            text += f"*{i}\\. {time}*\n"
            text += f"👤 {customer}\n"
            text += f"💇‍♂️ Barber: {barber}\n"
            text += f"✂️ Service: {service}\n\n"

        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            error_msg = f"Status {e.response.status_code}: {e.response.text[:200]}"
        logger.error(f"Error fetching tomorrow's appointments: {error_msg}")
        await update.message.reply_text(f"❌ Error fetching appointments: {escape_markdown(error_msg)}", parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and show today's statistics"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"{PUBLIC_API_BASE}/api/appointments/stats/"
            resp = await client.get(url)
            resp.raise_for_status()
            stats = resp.json()

        total = stats.get('total', 0)
        barbers = stats.get('by_barber', {})

        text = "📊 *Today's Statistics*\n\n"
        text += f"🧔‍♂️ Total appointments: *{total}*\n\n"

        if barbers:
            text += "✂️ *Breakdown by barber:*\n"
            for barber, count in barbers.items():
                barber_esc = escape_markdown(barber)
                text += f"• {barber_esc}: {count}\n"
        else:
            text += "😴 No appointments today\\."

        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            error_msg = f"Status {e.response.status_code}: {e.response.text[:200]}"
        logger.error(f"Error fetching stats: {error_msg}")
        await update.message.reply_text(f"❌ Error fetching stats: {escape_markdown(error_msg)}", parse_mode='Markdown')

def run_telegram_bot():
    """Run the Telegram bot polling worker"""
    logger.info("Starting Telegram bot polling worker")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("today", today_command))
    application.add_handler(CommandHandler("tomorrow", tomorrow_command))
    application.add_handler(CommandHandler("stats", stats_command))

    # Start polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

def run_fastapi():
    """Run the FastAPI server"""
    logger.info("Starting FastAPI server on 0.0.0.0:8787")
    uvicorn.run(app, host="0.0.0.0", port=8787, log_level="info")

if __name__ == "__main__":
    # Run FastAPI in a background thread
    fastapi_thread = Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()

    # Run Telegram bot in main thread
    run_telegram_bot()
