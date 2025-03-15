from flask import Blueprint, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models.comment import Comment
from models.post import Post
from extensions import db

comment_bp = Blueprint('comment', __name__)

@comment_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content')
    parent_id = request.form.get('parent_id')

    if not content:
        return jsonify({'success': False, 'message': 'Comment cannot be empty'}), 400

    new_comment = Comment(
        content=content,
        user_id=current_user.id,
        post_id=post_id,
        parent_id=parent_id if parent_id else None
    )

    db.session.add(new_comment)
    db.session.commit()

    # If it's an AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True, 
            'comment_id': new_comment.id
        })

    # Otherwise, redirect back to the post
    return redirect(url_for('main.view_post', post_id=post_id))

@comment_bp.route('/comment/<int:comment_id>/edit', methods=['POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # Check if the current user is the author or an admin
    if current_user.id != comment.user_id and not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    content = request.form.get('content')
    if not content:
        return jsonify({'success': False, 'message': 'Comment cannot be empty'}), 400

    comment.content = content
    db.session.commit()

    return redirect(url_for('main.view_post', post_id=comment.post_id))

@comment_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # Check if the current user is the author or an admin
    if current_user.id != comment.user_id and not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    db.session.delete(comment)
    db.session.commit()

    return redirect(url_for('main.view_post', post_id=comment.post_id))