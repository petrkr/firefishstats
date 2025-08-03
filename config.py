import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    CREDITAS_API_TOKEN = os.environ.get('CREDITAS_API_TOKEN')
    CREDITAS_ACCOUNT_ID = os.environ.get('CREDITAS_ACCOUNT_ID')
    CREDITAS_API_BASE_URL = os.environ.get('CREDITAS_API_BASE_URL', 'https://api.creditas.cz/oam/v1')
    TRANSACTIONS_FILE = os.environ.get('TRANSACTIONS_FILE', 'data/transactions.json')
    KNOWN_ACCOUNTS = set(os.environ.get('KNOWN_ACCOUNTS', '').split(',')) if os.environ.get('KNOWN_ACCOUNTS') else set()

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}