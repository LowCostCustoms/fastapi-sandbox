#!/bin/sh -e

exec poetry run uvicorn main:app "$@"
