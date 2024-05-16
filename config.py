import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

TOKEN: str = os.getenv("TOKEN")
if not TOKEN:
    print("[ERROR] TOKEN must be specified in the .env file.")
    sys.exit(1)
MIDAIR_SERVERS_API_URL: str = os.getenv("MIDAIR_SERVERS_API_URL")
if not MIDAIR_SERVERS_API_URL:
    print("[ERROR] MIDAIR_SERVERS_API_URL must be specified in the .env file.")
    sys.exit(1)
DB_NAME: str = os.getenv("DB_NAME")
if not MIDAIR_SERVERS_API_URL:
    print("[ERROR] DB_NAME must be specified in the .env file.")
    sys.exit(1)
