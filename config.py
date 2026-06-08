import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("8975105830:AAHSsz6kETM1gD-x2JnOlfVTeLOWMRp_8I4")
OWNER_IDS = list(map(int, os.getenv("8881305868", "").split(','))) if os.getenv("OWNER_IDS") else []
