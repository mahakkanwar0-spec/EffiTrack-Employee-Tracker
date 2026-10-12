
import os

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "effitrack")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
