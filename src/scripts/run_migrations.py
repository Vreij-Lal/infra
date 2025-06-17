'''
import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from dotenv import load_dotenv
from src.logger import logger

load_dotenv()

def get_engines():
    DATABASE_URL = os.getenv("DATABASE_URL")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
    
    if not DATABASE_URL or not MYSQL_DATABASE:
        raise ValueError("DATABASE_URL or MYSQL_DATABASE is missing")
    
    admin_url = DATABASE_URL.rsplit("/", 1)[0]
    admin_engine = create_engine(admin_url, pool_pre_ping=True, future=True)
    app_engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
    
    return admin_engine, app_engine, MYSQL_DATABASE

def wait_for_mysql(engine, max_retries=10, delay=3):
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ MySQL is ready")
            return True
        except OperationalError:
            logger.warning(f"⏳ Waiting for MySQL... ({i+1}/{max_retries})")
            time.sleep(delay)
    raise RuntimeError("❌ MySQL did not become ready in time")

def ensure_database_exists(admin_engine, db_name):
    try:
        with admin_engine.begin() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))
            conn.execute(text(f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{os.getenv('MYSQL_USER')}'@'%'"))
            logger.info(f"✅ Database `{db_name}` is ready")
    except SQLAlchemyError as e:
        logger.error(f"❌ Database creation failed: {e}")
        raise

def apply_migrations(app_engine):
    from src.sql.migrations.migrations import users, audit_logs
    
    try:
        with app_engine.begin() as conn:
            logger.info("Applying database migrations...")
            conn.execute(text(users))
            conn.execute(text(audit_logs))
            logger.info("✅ Migrations completed successfully")
    except SQLAlchemyError as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    try:
        admin_engine, app_engine, db_name = get_engines()
        wait_for_mysql(admin_engine)
        ensure_database_exists(admin_engine, db_name)
        apply_migrations(app_engine)
    except Exception as ex:
        logger.error(f"❌ Initialization failed: {ex}")
        exit(1)
'''
