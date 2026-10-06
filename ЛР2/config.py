import os

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))


def _database_url(env_var: str, default: str) -> str:
    url = os.environ.get(env_var, default)
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql+psycopg2://', 1)
    elif url.startswith('postgresql://'):
        url = url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    return url


class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')

    SQLALCHEMY_DATABASE_URI = _database_url(
        'DATABASE_URL',
        'postgresql+psycopg2://postgres:postgres@localhost:5432/menu_stolovoy',
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WTF_CSRF_ENABLED = True

    ITEMS_PER_PAGE = 20


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False 
    SQLALCHEMY_DATABASE_URI = _database_url(
        'TEST_DATABASE_URL',
        'postgresql+psycopg2://postgres:postgres@localhost:5432/menu_stolovoy_test',
    )


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
