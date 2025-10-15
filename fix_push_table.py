from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Drop and recreate
    db.session.execute(text("DROP TABLE push_subscriptions"))
    db.session.execute(text("""
        CREATE TABLE push_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint VARCHAR(500) UNIQUE NOT NULL,
            subscription_json TEXT NOT NULL,
            batch_name VARCHAR(10) NOT NULL,
            user_agent VARCHAR(200),
            ip_address VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_notified DATETIME,
            is_active BOOLEAN DEFAULT 1
        )
    """))
    db.session.execute(text("CREATE INDEX ix_push_subscriptions_endpoint ON push_subscriptions (endpoint)"))
    db.session.execute(text("CREATE INDEX ix_push_subscriptions_batch_name ON push_subscriptions (batch_name)"))
    db.session.execute(text("CREATE INDEX ix_push_subscriptions_is_active ON push_subscriptions (is_active)"))
    db.session.commit()
    print("✅ Table updated!")