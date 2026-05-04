import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-changeme-in-production'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'certchain',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'certchain_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'certchain_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'data' / 'db.sqlite3',
    }
}

AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']
# Utente personalizzato
AUTH_USER_MODEL = 'certchain.CustomUser'


# JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS':  True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

LANGUAGE_CODE = 'it-it'
TIME_ZONE = 'Europe/Rome'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ── Email (Gmail SMTP) ───────────────────────────────────────
import os
# Invece del backend SMTP, usa quello della console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#EMAIL_BACKEND      = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST         = 'smtp.gmail.com'
EMAIL_PORT         = 587
EMAIL_USE_TLS      = True
EMAIL_HOST_USER    = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD= os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
# ── Configurazione Blockchain ────────────────────────────────
# URL di Ganache (Assicurati che coincida con la porta del tuo terminale)
BLOCKCHAIN_NODE_URL = os.environ.get('BLOCKCHAIN_NODE_URL', 'http://127.0.0.1:8546')
ADMIN_PRIVATE_KEY = os.environ.get('PRIVATE_KEY_Admin')
ENTE_PRIVATE_KEY  = os.environ.get('PRIVATE_KEY_EnteCert')
AZIENDA_PRIVATE_KEY = os.environ.get('PRIVATE_KEY_Azienda')

# 1. Caricamento ABI (Indispensabile per far parlare MetaMask con il contratto)
import json
ABI_PATH = BASE_DIR / 'blockchain' / 'build' / 'contracts' / 'Contract_bn.json'
BLOCKCHAIN_CONTRACT_ABI = None

if ABI_PATH.exists():
    try:
        with open(ABI_PATH, 'r') as f:
            BLOCKCHAIN_CONTRACT_ABI = json.load(f).get('abi')
    except Exception as e:
        print(f"⚠️ Errore nel caricamento ABI: {e}")

# 2. Recupero Indirizzo Contratto
# Proviamo a leggerlo dal file generato dal deploy, altrimenti usiamo il fallback
ADDR_JSON_PATH = BASE_DIR / 'blockchain' / 'contract_address.json'
if ADDR_JSON_PATH.exists():
    try:
        with open(ADDR_JSON_PATH, 'r') as f:
            BLOCKCHAIN_CONTRACT_ADDRESS = json.load(f).get('address')
    except Exception:
        BLOCKCHAIN_CONTRACT_ADDRESS = "0x6587e9A33D2C633D6fE060867660C92898e28B1A" # Fallback
else:
    # Se il file non esiste ancora, mettiamo l'ultimo indirizzo noto
    BLOCKCHAIN_CONTRACT_ADDRESS = "0x6587e9A33D2C633D6fE060867660C92898e28B1A"

