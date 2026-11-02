#!/bin/sh
set -e
uv pip install --system "psycopg[binary]==3.2.*" "psycopg-pool==3.2.*"
