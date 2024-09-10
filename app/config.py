from pathlib import Path


class Config:
    db_path = Path(__file__).parent / "db" / "base.sqlite"
