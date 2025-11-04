#!/bin/bash
# Wrapper for send-telegram.py
# Usage: send-telegram.sh "message"

exec /usr/bin/python3 /usr/local/bin/send-telegram.py "$@"
