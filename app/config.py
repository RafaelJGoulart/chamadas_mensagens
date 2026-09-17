from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
BACKUPS_DIR = BASE_DIR / "backups"
LOGS_DIR = BASE_DIR / "logs"

DATA_DIR.mkdir(exist_ok=True)
BACKUPS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


class Config:
    SECRET_KEY = "sistema-chamadas-chave-local"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATA_DIR / 'sistema.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
