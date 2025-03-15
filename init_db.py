from flask import Flask
from extensions import db
from werkzeug.security import generate_password_hash

from app import create_app

app = create_app()

with app.app_context():
    from models.user import User
    from models.lua_script import LuaScript, ScriptCollaborator, LuaScriptVersion
    from models.lua_docs import LuaNamespace, LuaFunction, LuaParameter
    
    db.create_all()

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
    
    print("Database initialized successfully!")