from pytz import timezone
from decouple import config

# Database Secrets
DB_USER = config('DB_USER')
DB_HOST = config('DB_HOST')
DB_PORT = config('DB_PORT', cast=int, default=5432)
DB_PASS = config('DB_PASS')
DB_NAME = config('DB_NAME')

# JWT Secrets
SECRET_KEYS = config('SECRET_KEYS')
ALGORITHM = config('ALGORITHM')

ACCESS_TOKEN_TIME = config('ACCESS_TOKEN_TIME', cast=int)
REFRESH_TOKEN_TIME = config('REFRESH_TOKEN_TIME', cast=int)

# Upload file
UPLOAD_FOLDER = config('UPLOAD_FOLDER')

# Time zone
tashkent = timezone("Asia/Tashkent")

EMAIL_SENDER = config('SENDER_EMAIL')
EMAIL_SENDER_PASSWORD = config('SENDER_EMAIL_PASSWORD')

VONAGE_KEY = config('VONAGE_KEY')
VONAGE_SECRET = config('VONAGE_SECRET')