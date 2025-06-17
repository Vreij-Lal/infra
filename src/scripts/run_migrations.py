from sqlalchemy import text
from src.database.core import engine
from src.sql.migrations.migrations import users, audit_logs

print("✅ Connecting to DB and applying migrations...")

with engine.connect() as conn:
    conn.execute(text(users))
    conn.execute(text(audit_logs))

print("✅ Migrations completed successfully.")