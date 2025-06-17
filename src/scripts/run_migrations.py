import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

if not DATABASE_URL or not MYSQL_DATABASE:
    raise Exception("DATABASE_URL or MYSQL_DATABASE is missing")

admin_url = DATABASE_URL.rsplit("/", 1)[0]
admin_engine = create_engine(admin_url)

def create_database_if_not_exists():
    with admin_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}"))

def run_migrations():
    from src.database.core import engine
    from src.sql.migrations.migrations import users, audit_logs

    with engine.connect() as conn:
        conn.execute(text(users))
        conn.execute(text(audit_logs))

if __name__ == "__main__":
    try:
        create_database_if_not_exists()
        run_migrations()
        print("✅ Database and tables ready.")
    except OperationalError as e:
        print(f"❌ DB Error: {e}")