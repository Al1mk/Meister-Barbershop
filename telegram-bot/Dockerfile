FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Berlin

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    httpx \
    python-dotenv \
    python-telegram-bot==21.* \
    pytz

# Copy application code
COPY app.py /app/app.py
COPY .env /app/.env

# Expose port for FastAPI
EXPOSE 8787

# Run the application
CMD ["python", "app.py"]
