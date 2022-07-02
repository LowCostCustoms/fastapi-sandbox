#!/bin/sh -e

exec poetry run uvicorn main:app --host 0.0.0.0 "$@"
