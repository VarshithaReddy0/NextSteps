import os
from app import create_app, db
from app.models import Batch

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

# Add default batches during initialization (if not already present)
def seed_batches():
    with app.app_context():
        default_batches = ['2024', '2025', '2026']
        for name in default_batches:
            if not Batch.query.filter_by(name=name).first():
                db.session.add(Batch(name=name))
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_batches()  # Create default batches
    app.run(debug=True)