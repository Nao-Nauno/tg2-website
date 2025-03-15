from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from models.forum import ForumCategory, ForumTopic, ForumPost
from extensions import db

forum_bp = Blueprint('forum', __name__)

@forum_bp.route('/forum')
def forum_index():
    categories = ForumCategory.query.order_by(ForumCategory.order).all()
    return render_template('forum/index.html', categories=categories)

@forum_bp.route('/forum/category/<int:category_id>')
def forum_category(category_id):
    category = ForumCategory.query.get_or_404(category_id)
    topics = category.topics.order_by(ForumTopic.is_pinned.desc(), ForumTopic.created_at.desc()).all()
    return render_template('forum/category.html', category=category, topics=topics)

@forum_bp.route('/forum/topic/<int:topic_id>')
def forum_topic(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)
    posts = topic.posts.order_by(ForumPost.created_at.asc()).all()
    return render_template('forum/topic.html', topic=topic, posts=posts)

@forum_bp.route('/forum/topic/create', methods=['GET', 'POST'])
@login_required
def create_topic():
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        title = request.form.get('title')
        content = request.form.get('content')

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

        return redirect(url_for('forum.forum_topic', topic_id=topic.id))

    categories = ForumCategory.query.order_by(ForumCategory.order).all()
    return render_template('forum/create_topic.html', categories=categories)

@forum_bp.route('/forum/topic/<int:topic_id>/reply', methods=['POST'])
@login_required
def reply_topic(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)
    content = request.form.get('content')

    if not content:
        return redirect(url_for('forum.forum_topic', topic_id=topic_id))

    post = ForumPost(
        content=content,
        topic_id=topic_id,
        user_id=current_user.id
    )
    db.session.add(post)
    db.session.commit()

    return redirect(url_for('forum.forum_topic', topic_id=topic_id))