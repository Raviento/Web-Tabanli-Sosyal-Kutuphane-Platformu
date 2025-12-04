"""
Django settings for core project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv  # 1. .env dosyasını okumak için ekledik

# .env dosyasını yükle
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. GÜVENLİK AYARLARI (.env'den okur, yoksa varsayılanı kullanır)
SECRET_KEY = os.getenv('SECRET_KEY')

# Uyarı: Canlı sunucuda False olmalı, ama projende True kalsın.
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3. YENİ EKLENEN KÜTÜPHANELER
    'rest_framework',       # API (PDF Madde 13)
    'corsheaders',          # Frontend bağlantısı için (PDF Madde 18)
    'core',                 # Senin uygulamanın adı (Modelleri tanıması için şart!)
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', # 4. EN ÜSTE EKLENDİ (Zorunlu)
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 5. FRONTEND İÇİN İZİN (CORS)
CORS_ALLOW_ALL_ORIGINS = True  # Geliştirme aşamasında her yerden isteği kabul et

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# 6. VERİTABANI AYARI (PostgreSQL Bağlantısı)
# .env varsa oradan okur, yoksa varsayılan değerleri kullanır.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'), 
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# 7. DİL VE SAAT AYARLARI (Türkçe)
LANGUAGE_CODE = 'tr-tr'

TIME_ZONE = 'Europe/Istanbul'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = 'static/'

# 8. MEDYA DOSYALARI (Resim yükleme için şart) 
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- E-POSTA AYARLARI (GMAIL SMTP) ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# .env dosyasındaki isimleri kullanıyoruz:
EMAIL_HOST_USER = os.getenv('MAIL_RECOVER') 
EMAIL_HOST_PASSWORD = os.getenv('MAIL_RECOVER_PASSWORD') 
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER