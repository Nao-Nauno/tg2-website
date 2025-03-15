from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from extensions import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    bio = db.Column(db.Text)
    location = db.Column(db.String(100))
    title = db.Column(db.String(100))
    avatar_path = db.Column(db.String(255), default='images/default-avatar.png')
    banner_path = db.Column(db.String(255), default='images/default-banner.jpg')
    website = db.Column(db.String(200))
    discord = db.Column(db.String(100))
    steam_id = db.Column(db.String(100))
    favorite_profession = db.Column(db.String(100))
    owned_scripts = db.relationship('LuaScript', back_populates='owner', foreign_keys='LuaScript.owner_id')
    collaborating_scripts = db.relationship('ScriptCollaborator', backref='collaborator')

    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
        
    def set_password(self, password):
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def get_post_count(self):
        return self.posts.count()
    
    def get_comment_count(self):
        return self.comments.count()

    def get_scripts(self, include_collaborations=True):
        scripts = LuaScript.query.filter_by(owner_id=self.id).all()
        
        if include_collaborations:
            collab_scripts = [collab.script for collab in self.collaborating_scripts]
            scripts.extend(collab_scripts)
        
        return scripts