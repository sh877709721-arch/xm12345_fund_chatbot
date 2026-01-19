import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.config.settings import Settings
import logging
# Configure logging to show INFO level messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_embedding_model_default():
    settings = Settings()
    assert settings.EMBEDDING_MODEL == 'bge-m3'

def test_openai_base_url_loaded():
    settings = Settings()
    logging.info(settings.OPENAI_BASE_URL)
    assert settings.OPENAI_BASE_URL is not None
def test_openai_api_key_loaded():
    settings = Settings()
    
    assert settings.OPENAI_API_KEY is not None

def test_embedding_base_url_loaded():
    settings = Settings()
    logging.info(settings.EMBEDDING_BASE_URL)
    assert settings.EMBEDDING_BASE_URL is not None

def test_embedding_api_key_loaded():
    settings = Settings()
    assert settings.EMBEDDING_API_KEY is not None

def test_postgres_url_loaded():
    settings = Settings()
    assert settings.POSTGRES_URL is not None

def test_optional_fields_none_without_env():
    settings = Settings()
    assert settings.OPENAI_BASE_URL is not None
    assert settings.OPENAI_API_KEY is not None
    assert settings.EMBEDDING_BASE_URL is not None
    assert settings.EMBEDDING_API_KEY is not None
    assert settings.POSTGRES_URL is not None
