from extensions import db
from datetime import datetime
from enum import Enum
import json

class ScriptVisibility(Enum):
    PRIVATE = 'private'
    PUBLIC = 'public'
    UNLISTED = 'unlisted'  # Only accessible with direct link

class CollaboratorRole(Enum):
    VIEWER = 'viewer'
    EDITOR = 'editor'
    OWNER = 'owner'

class LuaScript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text, default="-- Your Lua script here\n\nfunction OnInit()\n  -- Initialization code\nend\n")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    visibility = db.Column(db.Enum(ScriptVisibility), default=ScriptVisibility.PRIVATE)
    version = db.Column(db.Integer, default=1)
    tags = db.Column(db.String(255))
    
    # Metadata for the script (game version, dependencies, etc.)
    metadata_json = db.Column(db.Text, default='{}')
    
    owner = db.relationship('User', back_populates='owned_scripts')
    collaborators = db.relationship('ScriptCollaborator', back_populates='script', cascade='all, delete-orphan')
    versions = db.relationship('LuaScriptVersion', back_populates='script', cascade='all, delete-orphan')
    
    def get_metadata(self):
        return json.loads(self.metadata_json)
    
    def set_metadata(self, metadata_dict):
        self.metadata_json = json.dumps(metadata_dict)
    
    def get_collaborator_role(self, user_id):
        if user_id == self.owner_id:
            return CollaboratorRole.OWNER
        
        collab = ScriptCollaborator.query.filter_by(script_id=self.id, user_id=user_id).first()
        return collab.role if collab else None
    
    def can_user_edit(self, user_id):
        role = self.get_collaborator_role(user_id)
        return role in [CollaboratorRole.OWNER, CollaboratorRole.EDITOR]
    
    def can_user_view(self, user_id):
        if self.visibility == ScriptVisibility.PUBLIC:
            return True
        
        role = self.get_collaborator_role(user_id)
        return role is not None

class ScriptCollaborator(db.Model):
    script_id = db.Column(db.Integer, db.ForeignKey('lua_script.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    role = db.Column(db.Enum(CollaboratorRole), default=CollaboratorRole.VIEWER)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    script = db.relationship('LuaScript', back_populates='collaborators')
    user = db.relationship('User')

class LuaScriptVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    script_id = db.Column(db.Integer, db.ForeignKey('lua_script.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment = db.Column(db.String(255))
    
    script = db.relationship('LuaScript', back_populates='versions')
    created_by = db.relationship('User')