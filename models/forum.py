from extensions import db
from datetime import datetime

class ForumCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    order = db.Column(db.Integer, default=0)
    topics = db.relationship('ForumTopic', backref='category', lazy='dynamic')
    
    def get_stats(self):
        topic_count = self.topics.count()
        post_count = sum(topic.posts.count() for topic in self.topics)
        latest_post = ForumPost.query.join(ForumTopic).filter(ForumTopic.category_id == self.id).order_by(ForumPost.created_at.desc()).first()
        return {
            'topic_count': topic_count,
            'post_count': post_count,
            'latest_post': latest_post
        }

class ForumTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('forum_category.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    
    posts = db.relationship('ForumPost', backref='topic', lazy='dynamic', cascade='all, delete-orphan')
    user = db.relationship('User')
    
    def get_last_post(self):
        return self.posts.order_by(ForumPost.created_at.desc()).first()

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('forum_topic.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User')