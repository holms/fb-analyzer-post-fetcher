#!/bin/bash
# Set default log level if not provided
LOG_LEVEL=${UVICORN_LOG_LEVEL:-info}

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8001 --log-level $LOG_LEVEL
