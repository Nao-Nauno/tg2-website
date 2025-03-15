from app import create_app
import os

app = create_app()

with app.app_context():
    from extensions import db
    from models.user import User
    from models.post import Post
    from werkzeug.security import generate_password_hash
    
    print("Dropping all tables...")
    db.drop_all()
    print("Creating all tables with updated schema...")
    db.create_all()
    
    # Create admin user
    print("Creating admin user...")
    admin = User(
        username='admin',
        email='admin@example.com',
        password=generate_password_hash('admin123'),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    
    print("Database has been reset with the new schema!")