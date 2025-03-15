import os
import functools
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models.post import Post
from models.forum import ForumCategory, ForumTopic
from extensions import db
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You must be an admin to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get posts for the dashboard
    posts = Post.query.order_by(Post.created_at.desc()).all()
    
    # Get forum categories
    forum_categories = ForumCategory.query.order_by(ForumCategory.order).all()
    
    return render_template('admin/dashboard.html', 
                           posts=posts, 
                           forum_categories=forum_categories)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/posts/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_post():
    if request.method == 'POST':
        print("POST request received for create_post")
        print(f"Files in request: {list(request.files.keys())}")
        
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category', 'other')
        tags = request.form.get('tags', '')
        featured = True if request.form.get('featured') else False
        
        if not title or not content:
            flash('Title and content are required.', 'error')
            return redirect(url_for('admin.create_post'))
        
        # Handle image upload
        image_path = None
        if 'image' in request.files:
            image = request.files['image']
            print(f"Image filename: {image.filename}")
            print(f"Image content type: {image.content_type if hasattr(image, 'content_type') else 'unknown'}")
            
            if image and image.filename != '':
                try:
                    # Make sure the upload directory exists
                    upload_dir = os.path.join(current_app.static_folder, 'uploads')
                    print(f"Upload directory: {upload_dir}")
                    
                    if not os.path.exists(upload_dir):
                        print(f"Creating upload directory: {upload_dir}")
                        os.makedirs(upload_dir)
                    
                    # Generate a unique filename
                    filename = secure_filename(image.filename)
                    unique_filename = f"{int(datetime.now().timestamp())}_{filename}"
                    print(f"Generated filename: {unique_filename}")
                    
                    # Save the file
                    image_path = 'uploads/' + unique_filename
                    full_path = os.path.join(current_app.static_folder, image_path)
                    print(f"Saving to: {full_path}")
                    
                    image.save(full_path)
                    
                    print(f"File saved successfully: {os.path.exists(full_path)}")
                    print(f"File size: {os.path.getsize(full_path) if os.path.exists(full_path) else 'N/A'} bytes")
                except Exception as e:
                    print(f"Error saving image: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    flash(f"Error uploading image: {str(e)}", 'error')
        else:
            print("No 'image' field found in request.files")
        
        # Create post
        post = Post(
            title=title,
            content=content,
            user_id=current_user.id,
            category=category,
            tags=tags,
            featured=featured,
            image_path=image_path
        )
        
        db.session.add(post)
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/create_post.html')

@admin_bp.route('/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category', 'other')
        tags = request.form.get('tags', '')
        featured = True if request.form.get('featured') else False
        
        if not title or not content:
            flash('Title and content are required.', 'error')
            return redirect(url_for('admin.edit_post', post_id=post.id))
        
        # Handle image upload
        if 'image' in request.files:
            image = request.files['image']
            if image and image.filename != '':
                # Delete old image if exists
                if post.image_path:
                    try:
                        old_image_path = os.path.join(current_app.static_folder, post.image_path)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    except Exception as e:
                        print(f"Error deleting old image: {str(e)}")
                
                # Generate a unique filename
                filename = secure_filename(image.filename)
                unique_filename = f"{int(datetime.now().timestamp())}_{filename}"
                
                # Ensure upload directory exists
                upload_dir = os.path.join(current_app.static_folder, 'uploads')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                # Save new image
                image_path = 'uploads/' + unique_filename
                full_path = os.path.join(current_app.static_folder, image_path)
                
                try:
                    image.save(full_path)
                    post.image_path = image_path
                    print(f"New image saved at: {full_path}")
                except Exception as e:
                    print(f"Error saving new image: {str(e)}")
                    flash(f"Error uploading image: {str(e)}", 'error')
        
        # Update post
        post.title = title
        post.content = content
        post.category = category
        post.tags = tags
        post.featured = featured
        post.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Post updated successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/edit_post.html', post=post)
    
@admin_bp.route('/posts/<int:post_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Delete associated image if exists
    if post.image_path:
        image_path = os.path.join(current_app.static_folder, post.image_path)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(post)
    db.session.commit()
    
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('admin.dashboard'))

# Forum Category Management Routes
@admin_bp.route('/forum/category/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_forum_category():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        order = request.form.get('order', 0)
        
        # Validate input
        if not name:
            flash('Category name is required.', 'error')
            return redirect(url_for('admin.create_forum_category'))
        
        # Create new category
        new_category = ForumCategory(
            name=name,
            description=description,
            order=int(order)
        )
        
        db.session.add(new_category)
        db.session.commit()
        
        flash('Forum category created successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/create_forum_category.html')

@admin_bp.route('/forum/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_forum_category(category_id):
    category = ForumCategory.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        category.order = request.form.get('order', 0)
        
        # Validate input
        if not category.name:
            flash('Category name is required.', 'error')
            return redirect(url_for('admin.edit_forum_category', category_id=category_id))
        
        db.session.commit()
        
        flash('Forum category updated successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/edit_forum_category.html', category=category)

@admin_bp.route('/forum/category/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_forum_category(category_id):
    category = ForumCategory.query.get_or_404(category_id)
    
    try:
        # First, delete all topics in this category
        ForumTopic.query.filter_by(category_id=category_id).delete()
        
        # Then delete the category
        db.session.delete(category)
        db.session.commit()
        
        flash('Forum category and its topics deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/forum/manage')
@login_required
@admin_required
def manage_forums():
    # Get all categories with their topic counts
    categories = ForumCategory.query.order_by(ForumCategory.order).all()
    
    return render_template('admin/manage_forums.html', categories=categories)