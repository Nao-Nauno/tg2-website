from app import create_app
import os

app = create_app()

with app.app_context():
    from extensions import db
    
    # Print the actual database URI
    print(f"Database URI: {db.engine.url}")
    
    # If it's a SQLite file (not in-memory), check if it exists
    if db.engine.url.drivername == 'sqlite' and not db.engine.url.database == ':memory:':
        db_path = db.engine.url.database
        if db_path.startswith('/'):
            # Absolute path
            full_path = db_path
        else:
            # Relative path (remove leading ///)
            if db_path.startswith('///'):
                db_path = db_path[3:]
            full_path = os.path.abspath(db_path)
        
        print(f"Database file path: {full_path}")
        if os.path.exists(full_path):
            print(f"✅ Database file exists")
            print(f"File size: {os.path.getsize(full_path)} bytes")
        else:
            print(f"❌ Database file does not exist")
    
    # Try to create the database if it doesn't exist
    print("Creating database tables...")
    db.create_all()
    print("Database tables created.")