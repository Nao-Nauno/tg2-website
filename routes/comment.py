from flask import Blueprint, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.comment import Comment
from models.post import Post
from datetime import datetime

comment_bp = Blueprint('comment', __name__)

@comment_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content')
    parent_id = request.form.get('parent_id')
    
    if not content:
        flash('Comment cannot be empty', 'error')
        return redirect(url_for('main.view_post', post_id=post_id))
    
    # Create comment
    comment = Comment(
        content=content,
        post_id=post_id,
        user_id=current_user.id,
        parent_id=parent_id if parent_id else None
    )
    
    db.session.add(comment)
    db.session.commit()
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Format creation time
        created_time = comment.created_at.strftime('%B %d, %Y at %H:%M')
        
        return jsonify({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'author': current_user.username,
                'author_avatar': current_user.avatar_path,
                'created_time': created_time
            }
        })
    
    flash('Your comment has been added!', 'success')
    return redirect(url_for('main.view_post', post_id=post_id))

@comment_bp.route('/comment/<int:comment_id>/edit', methods=['POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # Check if user is comment author
    if comment.user_id != current_user.id and not current_user.is_admin:
        flash('You can only edit your own comments', 'error')
        return redirect(url_for('main.view_post', post_id=comment.post_id))
    
    content = request.form.get('content')
    
    if not content:
        flash('Comment cannot be empty', 'error')
        return redirect(url_for('main.view_post', post_id=comment.post_id))
    
    # Update comment
    comment.content = content
    comment.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'updated': True
            }
        })
    
    flash('Your comment has been updated!', 'success')
    return redirect(url_for('main.view_post', post_id=comment.post_id))

@comment_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # Check if user is comment author or admin
    if comment.user_id != current_user.id and not current_user.is_admin:
        flash('You can only delete your own comments', 'error')
        return redirect(url_for('main.view_post', post_id=comment.post_id))
    
    post_id = comment.post_id
    
    # Delete comment
    db.session.delete(comment)
    db.session.commit()
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': 'Comment deleted successfully'
        })
    
    flash('Your comment has been deleted!', 'success')
    return redirect(url_for('main.view_post', post_id=post_id))