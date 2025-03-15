from datetime import datetime
from extensions import db

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), default='other')
    tags = db.Column(db.String(200))
    featured = db.Column(db.Boolean, default=False)
    image_path = db.Column(db.String(255))
    
    # Add relationship with comments
    comments = db.relationship('Comment', backref='post', lazy='dynamic', 
                               primaryjoin="and_(Comment.post_id==Post.id, Comment.parent_id==None)",
                               cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Post {self.title}>'
        
    def get_comment_count(self):
        return 1
        # return Comment.query.filter_by(post_id=self.id).count()