from extensions import db
from datetime import datetime

class LuaNamespace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    functions = db.relationship('LuaFunction', backref='namespace', lazy='dynamic')

class LuaFunction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    signature = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    example_code = db.Column(db.Text)
    namespace_id = db.Column(db.Integer, db.ForeignKey('lua_namespace.id'), nullable=False)
    added_in_version = db.Column(db.String(20))
    is_deprecated = db.Column(db.Boolean, default=False)
    deprecated_message = db.Column(db.Text)
    
    parameters = db.relationship('LuaParameter', backref='function', lazy='dynamic', cascade='all, delete-orphan')
    
    def full_signature(self):
        return f"{self.namespace.name}.{self.name}{self.signature}"

class LuaParameter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    param_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_optional = db.Column(db.Boolean, default=False)
    default_value = db.Column(db.String(100))
    function_id = db.Column(db.Integer, db.ForeignKey('lua_function.id'), nullable=False)
    
    def __repr__(self):
        optional = "optional " if self.is_optional else ""
        default = f" = {self.default_value}" if self.default_value else ""
        return f"{optional}{self.param_type} {self.name}{default}"