#!/bin/bash
gunicorn api.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
