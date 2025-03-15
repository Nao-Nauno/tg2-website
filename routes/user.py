from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from extensions import db
from models.user import User
from models.post import Post
from models.comment import Comment
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/user/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    # Get recent posts by user
    recent_posts = user.posts.order_by(Post.created_at.desc()).limit(5).all()
    
    # Get recent comments by user
    recent_comments = user.comments.order_by(Comment.created_at.desc()).limit(5).all()
    
    return render_template('user/profile.html', user=user, 
                           recent_posts=recent_posts, 
                           recent_comments=recent_comments)

@user_bp.route('/user/<username>/posts')
def user_posts(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.created_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('user/posts.html', user=user, posts=posts)

@user_bp.route('/user/<username>/comments')
def user_comments(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    comments = user.comments.order_by(Comment.created_at.desc()).paginate(page=page, per_page=15)
    
    return render_template('user/comments.html', user=user, comments=comments)

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Basic info
        current_user.bio = request.form.get('bio', '')
        current_user.location = request.form.get('location', '')
        current_user.title = request.form.get('title', '')
        current_user.website = request.form.get('website', '')
        current_user.discord = request.form.get('discord', '')
        current_user.steam_id = request.form.get('steam_id', '')
        current_user.favorite_profession = request.form.get('favorite_profession', '')
        
        # Handle avatar upload
        if 'avatar' in request.files:
            avatar = request.files['avatar']
            if avatar and avatar.filename != '':
                try:
                    # Make upload directory
                    upload_dir = os.path.join(current_app.static_folder, 'uploads/avatars')
                    if not os.path.exists(upload_dir):
                        os.makedirs(upload_dir)
                        
                    # Generate filename
                    filename = secure_filename(avatar.filename)
                    unique_filename = f"avatar_{current_user.id}_{int(datetime.now().timestamp())}_{filename}"
                    
                    # Save avatar
                    avatar_path = 'uploads/avatars/' + unique_filename
                    full_path = os.path.join(current_app.static_folder, avatar_path)
                    avatar.save(full_path)
                    
                    # Update user
                    current_user.avatar_path = avatar_path
                except Exception as e:
                    flash(f'Error uploading avatar: {str(e)}', 'error')
        
        # Handle banner upload
        if 'banner' in request.files:
            banner = request.files['banner']
            if banner and banner.filename != '':
                try:
                    # Make upload directory
                    upload_dir = os.path.join(current_app.static_folder, 'uploads/banners')
                    if not os.path.exists(upload_dir):
                        os.makedirs(upload_dir)
                        
                    # Generate filename
                    filename = secure_filename(banner.filename)
                    unique_filename = f"banner_{current_user.id}_{int(datetime.now().timestamp())}_{filename}"
                    
                    # Save banner
                    banner_path = 'uploads/banners/' + unique_filename
                    full_path = os.path.join(current_app.static_folder, banner_path)
                    banner.save(full_path)
                    
                    # Update user
                    current_user.banner_path = banner_path
                except Exception as e:
                    flash(f'Error uploading banner: {str(e)}', 'error')
        
        # Save changes
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('user.profile', username=current_user.username))
    
    return render_template('user/edit_profile.html')