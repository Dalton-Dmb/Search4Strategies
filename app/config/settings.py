from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
import os
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

@dataclass(frozen=True)
class Settings:
    root: Path
    data_dir: Path
    reports_dir: Path
    database_url: str
    mt5_path: str | None
    mt5_login: str | None
    mt5_password: str | None
    mt5_server: str | None

def load_yaml() -> dict:
    cfg = ROOT / "config.yaml"
    if not cfg.exists():
        return {}
    with cfg.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def get_settings() -> Settings:
    data_dir = ROOT / os.getenv("DATA_DIR", "storage/parquet")
    reports_dir = ROOT / os.getenv("REPORTS_DIR", "storage/reports")
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        root=ROOT,
        data_dir=data_dir,
        reports_dir=reports_dir,
        database_url=os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'storage/database/search4strategies.db'}"),
        mt5_path=os.getenv("MT5_PATH") or None,
        mt5_login=os.getenv("MT5_LOGIN") or None,
        mt5_password=os.getenv("MT5_PASSWORD") or None,
        mt5_server=os.getenv("MT5_SERVER") or None,
    )

