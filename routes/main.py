from flask import Blueprint, render_template, request
from models.post import Post
from models.comment import Comment
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=5)
    return render_template('index.html', posts=posts, now=datetime.now())

@main_bp.route('/about')
def about():
    return render_template('about.html', now=datetime.now())

@main_bp.route('/reforged')
def reforged():
    return render_template('reforged.html', now=datetime.now())

@main_bp.route('/features')
def features():
    return render_template('features.html', now=datetime.now())

@main_bp.route('/download')
def download():
    return render_template('download.html', now=datetime.now())

@main_bp.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Fetch top-level comments (without parent) ordered by creation time
    comments = Comment.query.filter_by(post_id=post_id, parent_id=None).order_by(Comment.created_at.asc()).all()
    
    # Find related posts (simple implementation)
    related_posts = Post.query.filter(Post.id != post_id, Post.category == post.category).limit(3).all()
    
    return render_template('post/view.html', 
                           post=post, 
                           comments=comments, 
                           related_posts=related_posts)