import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

# Setup basic logging to stderr for early initialization
import os
initial_log_level = os.environ.get("LOG_LEVEL", "INFO")
numeric_level = getattr(logging, initial_log_level.upper(), logging.INFO)
logging.basicConfig(level=numeric_level, stream=sys.stderr, format='%(levelname)-5.5s [%(name)s] %(message)s')
logger = logging.getLogger(__name__)


def _looks_like_placeholder_secret(value: str) -> bool:
    lowered = value.strip().lower()
    placeholders = {
        "changeme",
        "replace-me",
        "replace_this",
        "replace-this",
        "your-secret-here",
        "secret",
        "password",
        "admin12345!",
    }
    if lowered in placeholders:
        return True
    if any(marker in lowered for marker in ("example", "placeholder", "generate-a-random", "your-llm-api-key")):
        return True
    unique_chars = len(set(lowered))
    return unique_chars < 10

def check_writable_dir(path: str) -> bool:
    try:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        # Check writable
        test_file = os.path.join(path, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True
    except Exception:
        return False

class Settings:
    def __init__(self):
        errors = []
        
        # REQUIRED VARIABLES
        self.DATABASE_URL = os.environ.get("DATABASE_URL")
        self.JWT_SECRET = os.environ.get("JWT_SECRET")
        self.JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM")
        self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
        self.LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")
        self.LLM_ENDPOINT = os.environ.get("LLM_ENDPOINT")
        self.LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME")
        self.LLM_API_KEY = os.environ.get("LLM_API_KEY")
        self.LLM_TIMEOUT_SECONDS = os.environ.get("LLM_TIMEOUT_SECONDS")
        self.LLM_OLLAMA_TIMEOUT_SECONDS = os.environ.get("LLM_OLLAMA_TIMEOUT_SECONDS", "180")
        self.LLM_TEMPERATURE = os.environ.get("LLM_TEMPERATURE", "0.0")
        self.LLM_JSON_MODE = os.environ.get("LLM_JSON_MODE", "true")
        self.LLM_PAYLOAD_MODE = os.environ.get("LLM_PAYLOAD_MODE", "full")
        self.LLM_KEEP_ALIVE = os.environ.get("LLM_KEEP_ALIVE", "10m")
        self.LLM_LOAD_WAIT_TIMEOUT_SECONDS = os.environ.get("LLM_LOAD_WAIT_TIMEOUT_SECONDS", "120")
        self.LLM_LOAD_POLL_INTERVAL_SECONDS = os.environ.get("LLM_LOAD_POLL_INTERVAL_SECONDS", "5")
        self.PARSER_ENGINE_VERSION = os.environ.get("PARSER_ENGINE_VERSION", "v2")
        self.UPLOAD_DIRECTORY = os.environ.get("UPLOAD_DIRECTORY")
        self.MAX_UPLOAD_SIZE_MB = os.environ.get("MAX_UPLOAD_SIZE_MB")
        self.APP_ENV = os.environ.get("APP_ENV")
        self.LOG_LEVEL = os.environ.get("LOG_LEVEL")
        self.DEV_BOOTSTRAP_ADMIN = os.environ.get("DEV_BOOTSTRAP_ADMIN", "false")
        self.DEV_ADMIN_EMAIL = os.environ.get("DEV_ADMIN_EMAIL")
        self.DEV_ADMIN_PASSWORD = os.environ.get("DEV_ADMIN_PASSWORD")
        self.DEV_ADMIN_NAME = os.environ.get("DEV_ADMIN_NAME")
        self.SESSION_COOKIE_NAME = os.environ.get("SESSION_COOKIE_NAME", "agis_session")
        self.SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "lax")
        self.CSRF_COOKIE_NAME = os.environ.get("CSRF_COOKIE_NAME", "agis_csrf")
        self.CSRF_HEADER_NAME = os.environ.get("CSRF_HEADER_NAME", "X-CSRF-Token")
        self.CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
        self.LLM_DISABLE_LIVE_CALLS = os.environ.get("LLM_DISABLE_LIVE_CALLS", "false")

        # VALIDATE PRESENCE
        required_vars = [
            ("DATABASE_URL", self.DATABASE_URL), ("JWT_SECRET", self.JWT_SECRET),
            ("JWT_ALGORITHM", self.JWT_ALGORITHM), ("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
            ("LLM_ENDPOINT", self.LLM_ENDPOINT), ("LLM_MODEL_NAME", self.LLM_MODEL_NAME),
            ("LLM_TIMEOUT_SECONDS", self.LLM_TIMEOUT_SECONDS),
            ("UPLOAD_DIRECTORY", self.UPLOAD_DIRECTORY), ("MAX_UPLOAD_SIZE_MB", self.MAX_UPLOAD_SIZE_MB),
            ("APP_ENV", self.APP_ENV), ("LOG_LEVEL", self.LOG_LEVEL)
        ]

        for name, val in required_vars:
            if val is None or val.strip() == "":
                errors.append(f"Missing required environment variable: {name}")

        if self.LLM_PROVIDER in {"openai", "openrouter", "openai_compatible"}:
            if self.LLM_API_KEY is None or self.LLM_API_KEY.strip() == "":
                errors.append("Missing required environment variable: LLM_API_KEY")

        # OPTIONAL VARIABLES
        raw_db_pool = os.environ.get("DB_POOL_SIZE")
        if raw_db_pool:
            self.DB_POOL_SIZE = int(raw_db_pool)
        else:
            self.DB_POOL_SIZE = 5
            logger.info("Applying default for DB_POOL_SIZE: 5")

        raw_db_overflow = os.environ.get("DB_MAX_OVERFLOW")
        if raw_db_overflow:
            self.DB_MAX_OVERFLOW = int(raw_db_overflow)
        else:
            self.DB_MAX_OVERFLOW = 10
            logger.info("Applying default for DB_MAX_OVERFLOW: 10")

        # SEMANTIC VALIDATION
        if self.DATABASE_URL:
            if not (self.DATABASE_URL.startswith("postgresql://") or self.DATABASE_URL.startswith("postgresql+psycopg2://")):
                errors.append("DATABASE_URL must use synchronous prefix (postgresql:// or postgresql+psycopg2://)")

        if self.JWT_SECRET and len(self.JWT_SECRET) < 32:
            errors.append("JWT_SECRET must be at least 32 characters long")
        elif self.JWT_SECRET and _looks_like_placeholder_secret(self.JWT_SECRET):
            errors.append("JWT_SECRET must not use a weak or placeholder value")

        if self.JWT_ALGORITHM and self.JWT_ALGORITHM not in {"HS256", "HS384", "HS512"}:
            errors.append("JWT_ALGORITHM must be one of {HS256, HS384, HS512}")

        if self.LLM_PROVIDER not in {"ollama", "openai", "openrouter", "openai_compatible"}:
            errors.append("LLM_PROVIDER must be one of {ollama, openai, openrouter, openai_compatible}")

        if self.LLM_PAYLOAD_MODE not in {"full", "compact"}:
            errors.append("LLM_PAYLOAD_MODE must be one of {full, compact}")

        self.PARSER_ENGINE_VERSION = str(self.PARSER_ENGINE_VERSION).strip().lower()
        if self.PARSER_ENGINE_VERSION not in {"v1", "v2"}:
            errors.append("PARSER_ENGINE_VERSION must be one of {v1, v2}")

        if self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES:
            try:
                self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
                if self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
                    errors.append("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be > 0")
            except ValueError:
                errors.append("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be an integer")

        if self.LLM_ENDPOINT:
            if self.APP_ENV == "development" and self.LLM_ENDPOINT.startswith("http://"):
                pass  # Allowed in development for local/containerized Ollama
            elif not self.LLM_ENDPOINT.startswith("https://"):
                errors.append("LLM_ENDPOINT must be an HTTPS URL (unless in development)")

        if self.LLM_TIMEOUT_SECONDS:
            try:
                self.LLM_TIMEOUT_SECONDS = int(self.LLM_TIMEOUT_SECONDS)
                if self.LLM_TIMEOUT_SECONDS <= 0:
                    errors.append("LLM_TIMEOUT_SECONDS must be > 0")
            except ValueError:
                errors.append("LLM_TIMEOUT_SECONDS must be an integer")

        try:
            self.LLM_OLLAMA_TIMEOUT_SECONDS = int(self.LLM_OLLAMA_TIMEOUT_SECONDS)
            if self.LLM_OLLAMA_TIMEOUT_SECONDS <= 0:
                errors.append("LLM_OLLAMA_TIMEOUT_SECONDS must be > 0")
        except ValueError:
            errors.append("LLM_OLLAMA_TIMEOUT_SECONDS must be an integer")

        try:
            self.LLM_TEMPERATURE = float(self.LLM_TEMPERATURE)
        except ValueError:
            errors.append("LLM_TEMPERATURE must be a float")

        self.LLM_JSON_MODE = str(self.LLM_JSON_MODE).strip().lower() in {"1", "true", "yes", "on"}

        try:
            self.LLM_LOAD_WAIT_TIMEOUT_SECONDS = int(self.LLM_LOAD_WAIT_TIMEOUT_SECONDS)
            if self.LLM_LOAD_WAIT_TIMEOUT_SECONDS <= 0:
                errors.append("LLM_LOAD_WAIT_TIMEOUT_SECONDS must be > 0")
        except ValueError:
            errors.append("LLM_LOAD_WAIT_TIMEOUT_SECONDS must be an integer")

        try:
            self.LLM_LOAD_POLL_INTERVAL_SECONDS = int(self.LLM_LOAD_POLL_INTERVAL_SECONDS)
            if self.LLM_LOAD_POLL_INTERVAL_SECONDS <= 0:
                errors.append("LLM_LOAD_POLL_INTERVAL_SECONDS must be > 0")
        except ValueError:
            errors.append("LLM_LOAD_POLL_INTERVAL_SECONDS must be an integer")

        if self.MAX_UPLOAD_SIZE_MB:
            try:
                self.MAX_UPLOAD_SIZE_MB = int(self.MAX_UPLOAD_SIZE_MB)
                if self.MAX_UPLOAD_SIZE_MB <= 0:
                    errors.append("MAX_UPLOAD_SIZE_MB must be > 0")
            except ValueError:
                errors.append("MAX_UPLOAD_SIZE_MB must be an integer")

        if self.APP_ENV and self.APP_ENV not in {"development", "production"}:
            errors.append("APP_ENV must be 'development' or 'production'")

        self.DEV_BOOTSTRAP_ADMIN = str(self.DEV_BOOTSTRAP_ADMIN).strip().lower() in {"1", "true", "yes", "on"}
        self.LLM_DISABLE_LIVE_CALLS = str(self.LLM_DISABLE_LIVE_CALLS).strip().lower() in {"1", "true", "yes", "on"}

        if self.LOG_LEVEL and self.LOG_LEVEL not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            errors.append("LOG_LEVEL must be one of {DEBUG, INFO, WARNING, ERROR, CRITICAL}")

        if self.SESSION_COOKIE_SAMESITE not in {"lax", "strict", "none"}:
            errors.append("SESSION_COOKIE_SAMESITE must be one of {lax, strict, none}")
        if not self.CSRF_COOKIE_NAME or not self.CSRF_COOKIE_NAME.strip():
            errors.append("CSRF_COOKIE_NAME must not be empty")
        if not self.CSRF_HEADER_NAME or not self.CSRF_HEADER_NAME.strip():
            errors.append("CSRF_HEADER_NAME must not be empty")
        self.CSRF_TRUSTED_ORIGINS = [
            origin.strip()
            for origin in self.CSRF_TRUSTED_ORIGINS.split(",")
            if origin.strip()
        ]

        if self.DEV_BOOTSTRAP_ADMIN:
            if self.APP_ENV != "development":
                errors.append("DEV_BOOTSTRAP_ADMIN can only be enabled in development")
            if not self.DEV_ADMIN_EMAIL or not self.DEV_ADMIN_PASSWORD or not self.DEV_ADMIN_NAME:
                errors.append("DEV_BOOTSTRAP_ADMIN requires DEV_ADMIN_EMAIL, DEV_ADMIN_PASSWORD, and DEV_ADMIN_NAME")

        if self.DEV_ADMIN_PASSWORD:
            if len(self.DEV_ADMIN_PASSWORD) < 8:
                errors.append("DEV_ADMIN_PASSWORD must be at least 8 characters long")
            elif _looks_like_placeholder_secret(self.DEV_ADMIN_PASSWORD):
                errors.append("DEV_ADMIN_PASSWORD must not use a weak or placeholder value")

        if self.APP_ENV != "development":
            if self.DEV_BOOTSTRAP_ADMIN:
                errors.append("DEV_BOOTSTRAP_ADMIN must be disabled outside development")
            if any(value for value in (self.DEV_ADMIN_EMAIL, self.DEV_ADMIN_PASSWORD, self.DEV_ADMIN_NAME)):
                errors.append("DEV_ADMIN_* settings must not be configured outside development")

        if self.UPLOAD_DIRECTORY:
            self.UPLOAD_DIRECTORY = os.path.abspath(self.UPLOAD_DIRECTORY)
            if not check_writable_dir(self.UPLOAD_DIRECTORY):
                errors.append(f"UPLOAD_DIRECTORY ({self.UPLOAD_DIRECTORY}) is not writable or cannot be created")

        # IF ERRORS EXIST, FAIL STARTUP
        if errors:
            for error in errors:
                logger.error(f"Configuration Error: {error}")
            sys.exit(1)

        # REDACT AND LOG
        logger.info(f"Configuration loaded. APP_ENV={self.APP_ENV}, LOG_LEVEL={self.LOG_LEVEL}")
        logger.info("DATABASE_URL: ***[REDACTED]***")
        logger.info("JWT_SECRET: ***[REDACTED]***")
        logger.info(f"JWT_ALGORITHM: {self.JWT_ALGORITHM}")
        logger.info(f"LLM_PROVIDER: {self.LLM_PROVIDER}")
        logger.info(f"LLM_PAYLOAD_MODE: {self.LLM_PAYLOAD_MODE}")
        logger.info(f"PARSER_ENGINE_VERSION: {self.PARSER_ENGINE_VERSION}")
        logger.info(f"LLM_ENDPOINT: {self.LLM_ENDPOINT}")
        logger.info(f"LLM_MODEL_NAME: {self.LLM_MODEL_NAME}")
        logger.info("LLM_API_KEY: ***[REDACTED]***")

settings = Settings()
