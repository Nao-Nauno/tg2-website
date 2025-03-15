from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models.forum import ForumCategory, ForumTopic, ForumPost
from extensions import db

forum_bp = Blueprint('forum', __name__, url_prefix='/forum')

@forum_bp.route('/')
def forum_index():
    categories = ForumCategory.query.order_by(ForumCategory.order).all()
    return render_template('forum/index.html', categories=categories)

@forum_bp.route('/category/<int:category_id>')
def forum_category(category_id):
    category = ForumCategory.query.get_or_404(category_id)
    topics = category.topics.order_by(ForumTopic.is_pinned.desc(), ForumTopic.created_at.desc()).all()
    return render_template('forum/category.html', category=category, topics=topics)

@forum_bp.route('/topic/<int:topic_id>')
def forum_topic(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)
    
    # Increment view count
    topic.views += 1
    db.session.commit()
    
    posts = topic.posts.order_by(ForumPost.created_at.asc()).all()
    return render_template('forum/topic.html', topic=topic, posts=posts)

@forum_bp.route('/create_topic', methods=['GET', 'POST'])
@login_required
def create_topic():
    categories = ForumCategory.query.order_by(ForumCategory.order).all()
    
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        title = request.form.get('title')
        content = request.form.get('content')
        
        # Validate input
        if not title or not content or not category_id:
            flash('Title, content, and category are required.', 'error')
            return redirect(url_for('forum.create_topic'))
        
        # Create new topic
        topic = ForumTopic(
            title=title,
            category_id=category_id,
            user_id=current_user.id
        )
        db.session.add(topic)
        db.session.flush()  # To get the topic ID
        
        # Create first post
        first_post = ForumPost(
            content=content,
            topic_id=topic.id,
            user_id=current_user.id
        )
        db.session.add(first_post)
        db.session.commit()
        
        flash('Topic created successfully!', 'success')
        return redirect(url_for('forum.forum_topic', topic_id=topic.id))
    
    return render_template('forum/create_topic.html', categories=categories)

@forum_bp.route('/topic/<int:topic_id>/reply', methods=['POST'])
@login_required
def reply_topic(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)
    content = request.form.get('content')
    
    if not content:
        flash('Reply content cannot be empty.', 'error')
        return redirect(url_for('forum.forum_topic', topic_id=topic_id))
    
    # Create new post
    new_post = ForumPost(
        content=content,
        topic_id=topic_id,
        user_id=current_user.id
    )
    db.session.add(new_post)
    db.session.commit()
    
    flash('Reply posted successfully!', 'success')
    return redirect(url_for('forum.forum_topic', topic_id=topic_id))

@forum_bp.route('/topic/<int:topic_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_topic(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)
    
    # Check permissions
    if current_user.id != topic.user_id and not current_user.is_admin:
        flash('You do not have permission to edit this topic.', 'error')
        return redirect(url_for('forum.forum_topic', topic_id=topic_id))
    
    if request.method == 'POST':
        topic.title = request.form.get('title')
        db.session.commit()
        
        flash('Topic updated successfully!', 'success')
        return redirect(url_for('forum.forum_topic', topic_id=topic_id))
    
    return render_template('forum/edit_topic.html', topic=topic)

@forum_bp.route('/topic/<int:topic_id>/delete', methods=['POST'])
@login_required
def delete_topic(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)
    
    # Check permissions
    if current_user.id != topic.user_id and not current_user.is_admin:
        flash('You do not have permission to delete this topic.', 'error')
        return redirect(url_for('forum.forum_topic', topic_id=topic_id))
    
    # Delete all posts in the topic
    ForumPost.query.filter_by(topic_id=topic_id).delete()
    
    # Delete the topic
    db.session.delete(topic)
    db.session.commit()
    
    flash('Topic deleted successfully!', 'success')
    return redirect(url_for('forum.forum_index'))

@forum_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    
    # Check permissions
    if current_user.id != post.user_id and not current_user.is_admin:
        flash('You do not have permission to edit this post.', 'error')
        return redirect(url_for('forum.forum_topic', topic_id=post.topic_id))
    
    if request.method == 'POST':
        post.content = request.form.get('content')
        db.session.commit()
        
        flash('Post updated successfully!', 'success')
        return redirect(url_for('forum.forum_topic', topic_id=post.topic_id))
    
    return render_template('forum/edit_post.html', post=post)

@forum_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    topic_id = post.topic_id
    
    # Check permissions
    if current_user.id != post.user_id and not current_user.is_admin:
        flash('You do not have permission to delete this post.', 'error')
        return redirect(url_for('forum.forum_topic', topic_id=topic_id))
    
    # Check if this is the first post in the topic
    first_post = ForumPost.query.filter_by(topic_id=topic_id).order_by(ForumPost.created_at).first()
    
    if post.id == first_post.id:
        # If this is the first post, delete the entire topic
        ForumPost.query.filter_by(topic_id=topic_id).delete()
        topic = ForumTopic.query.get(topic_id)
        db.session.delete(topic)
        db.session.commit()
        
        flash('Topic deleted as the first post was deleted.', 'success')
        return redirect(url_for('forum.forum_index'))
    
    # Delete the post
    db.session.delete(post)
    db.session.commit()
    
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('forum.forum_topic', topic_id=topic_id))