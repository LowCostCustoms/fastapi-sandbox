#!/bin/sh -e

exec poetry run alembic upgrade head
