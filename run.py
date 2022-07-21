from dotenv import load_dotenv
import os
from web import *

load_dotenv("./data/.env")

debug = (os.getenv("ENVIRONMENT") == "DEBUG")

if debug:
    run(port=5000)
else:
    run(host="0.0.0.0", port=80)