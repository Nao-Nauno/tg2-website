from flask import Flask
from extensions import db
from werkzeug.security import generate_password_hash
from app import create_app
app = create_app()

with app.app_context():
    from models.user import User
    from models.lua_script import LuaScript, ScriptCollaborator, LuaScriptVersion
    from models.lua_docs import LuaNamespace, LuaFunction, LuaParameter
    from models.forum import ForumCategory, ForumTopic, ForumPost
    
    db.create_all()

    # Create admin user
    admin = User.query.filter_by(username='naonauno').first()
    if not admin:
        admin = User(
            username='naonauno',
            email='desk.nao@gmail.com',
            password=generate_password_hash('2opcydornetnekipceppyy201'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
    else:
        print("Admin user already exists!")

    # Create default forum categories
    default_categories = [
        {"name": "General Discussion", "description": "General chat and discussions about The Guild 2: Renaissance", "order": 1},
        {"name": "Mod Support", "description": "Technical support and discussions about the Reforged Mod", "order": 2},
        {"name": "Strategies", "description": "Share and discuss gameplay strategies", "order": 3},
        {"name": "Community Showcase", "description": "Share your achievements, screenshots, and stories", "order": 4}
    ]

    for category_data in default_categories:
        existing_category = ForumCategory.query.filter_by(name=category_data['name']).first()
        if not existing_category:
            new_category = ForumCategory(**category_data)
            db.session.add(new_category)
    
    db.session.commit()
    print("Default forum categories created successfully!")
    
    print("Database initialized successfully!")