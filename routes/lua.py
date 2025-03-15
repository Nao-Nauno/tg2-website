from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
import json
import os
from datetime import datetime
from extensions import db
from models.lua_script import LuaScript, LuaScriptVersion, ScriptCollaborator, ScriptVisibility, CollaboratorRole
from models.user import User

lua_bp = Blueprint('lua', __name__, url_prefix='/lua')

@lua_bp.route('/docs')
def docs():
    from models.lua_docs import LuaNamespace
    namespaces = LuaNamespace.query.all()
    
    # Calculate total function count
    total_functions = 0
    for namespace in namespaces:
        total_functions += namespace.functions.count()
    
    return render_template('lua/docs.html', namespaces=namespaces, total_functions=total_functions)

@lua_bp.route('/scripts')
def script_library():
    public_scripts = LuaScript.query.filter_by(visibility=ScriptVisibility.PUBLIC).all()
    
    user_scripts = []
    if current_user.is_authenticated:
        user_scripts = LuaScript.query.filter_by(owner_id=current_user.id).all()
        collab_scripts = [collab.script for collab in current_user.collaborating_scripts]
        scripts = list(set(public_scripts + user_scripts + collab_scripts))
    else:
        scripts = public_scripts
    
    return render_template('lua/library.html', scripts=scripts)

@lua_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_script():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')
        visibility = ScriptVisibility(request.form.get('visibility', 'private'))
        tags = request.form.get('tags', '')
        
        # Create the script
        script = LuaScript(
            title=title,
            description=description,
            owner_id=current_user.id,
            visibility=visibility,
            tags=tags
        )
        
        # Parse metadata if provided
        metadata = {}
        if 'metadata' in request.form and request.form['metadata']:
            try:
                metadata = json.loads(request.form['metadata'])
            except json.JSONDecodeError:
                flash('Invalid metadata format', 'error')
                return render_template('lua/create_script.html')
        
        script.set_metadata(metadata)
        
        # Create initial version
        content = request.form.get('content', "-- Your Lua script here\n\nfunction OnInit()\n  -- Initialization code\nend\n")
        script.content = content
        
        version = LuaScriptVersion(
            script=script,
            version_number=1,
            content=content,
            created_by_id=current_user.id,
            comment="Initial version"
        )
        
        db.session.add(script)
        db.session.add(version)
        db.session.commit()
        
        flash('Script created successfully!', 'success')
        return redirect(url_for('lua.edit_script', script_id=script.id))
    
    return render_template('lua/create_script.html')

@lua_bp.route('/edit/<int:script_id>')
@login_required
def edit_script(script_id):
    script = LuaScript.query.get_or_404(script_id)
    
    # Check permissions
    if not script.can_user_edit(current_user.id) and script.visibility != ScriptVisibility.PUBLIC:
        flash('You do not have permission to edit this script', 'error')
        return redirect(url_for('lua.script_library'))
    
    # Get collaborator statuses for display
    # In a real app, you'd get this from your WebSocket connection manager
    collaborator_statuses = {}  # User ID -> status (online/offline)
    
    # Pass CollaboratorRole to the template
    return render_template('lua/edit_script.html', 
                          script=script, 
                          collaborator_statuses=collaborator_statuses,
                          CollaboratorRole=CollaboratorRole)

@lua_bp.route('/save/<int:script_id>', methods=['POST'])
@login_required
def save_script(script_id):
    script = LuaScript.query.get_or_404(script_id)
    
    # Check permissions
    if not script.can_user_edit(current_user.id):
        return jsonify({'success': False, 'error': 'Permission denied'})
    
    content = request.json.get('content')
    create_new_version = request.json.get('create_new_version', False)
    version_comment = request.json.get('comment', '')
    
    # Update the script content
    script.content = content
    script.updated_at = datetime.utcnow()
    
    # Create a new version if requested
    if create_new_version:
        script.version += 1
        
        version = LuaScriptVersion(
            script=script,
            version_number=script.version,
            content=content,
            created_by_id=current_user.id,
            comment=version_comment
        )
        
        db.session.add(version)
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'version': script.version,
        'updated_at': script.updated_at.isoformat()
    })

@lua_bp.route('/api/scripts/<int:script_id>/collaborators', methods=['POST'])
@login_required
def add_collaborator(script_id):
    script = LuaScript.query.get_or_404(script_id)
    
    # Check permissions - only the owner can add collaborators
    if script.owner_id != current_user.id:
        return jsonify({'success': False, 'error': 'Only the owner can add collaborators'})
    
    username = request.json.get('username')
    role = request.json.get('role')
    
    # Find the user
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'success': False, 'error': 'User not found'})
    
    # Don't add the owner as a collaborator
    if user.id == script.owner_id:
        return jsonify({'success': False, 'error': 'Cannot add the owner as a collaborator'})
    
    # Check if already a collaborator
    existing = ScriptCollaborator.query.filter_by(script_id=script.id, user_id=user.id).first()
    if existing:
        existing.role = CollaboratorRole(role)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Collaborator role updated'})
    
    # Add new collaborator
    collaborator = ScriptCollaborator(
        script_id=script.id,
        user_id=user.id,
        role=CollaboratorRole(role)
    )
    
    db.session.add(collaborator)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Collaborator added successfully'})

@lua_bp.route('/api/scripts/<int:script_id>/versions/<int:version_number>')
@login_required
def get_script_version(script_id, version_number):
    script = LuaScript.query.get_or_404(script_id)
    
    # Check permissions
    if not script.can_user_view(current_user.id) and script.visibility != ScriptVisibility.PUBLIC:
        return jsonify({'success': False, 'error': 'Permission denied'})
    
    version = LuaScriptVersion.query.filter_by(script_id=script.id, version_number=version_number).first()
    if not version:
        return jsonify({'success': False, 'error': 'Version not found'})
    
    return jsonify({
        'success': True,
        'version': version.version_number,
        'content': version.content,
        'created_at': version.created_at.isoformat(),
        'created_by': version.created_by.username,
        'comment': version.comment
    })

@lua_bp.route('/api/scripts/<int:script_id>/restore/<int:version_number>', methods=['POST'])
@login_required
def restore_script_version(script_id, version_number):
    script = LuaScript.query.get_or_404(script_id)
    
    # Check permissions
    if not script.can_user_edit(current_user.id):
        return jsonify({'success': False, 'error': 'Permission denied'})
    
    version = LuaScriptVersion.query.filter_by(script_id=script.id, version_number=version_number).first()
    if not version:
        return jsonify({'success': False, 'error': 'Version not found'})
    
    # Create a new version based on the old one
    script.version += 1
    script.content = version.content
    
    new_version = LuaScriptVersion(
        script=script,
        version_number=script.version,
        content=version.content,
        created_by_id=current_user.id,
        comment=f"Restored from version {version_number}"
    )
    
    db.session.add(new_version)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Restored to version {version_number}',
        'new_version': script.version
    })

@lua_bp.route('/api/function/<int:function_id>')
def get_function_details(function_id):
    from models.lua_docs import LuaFunction, LuaParameter
    
    function = LuaFunction.query.get_or_404(function_id)
    
    # Convert to JSON-serializable format
    params = []
    for param in function.parameters:
        params.append({
            "name": param.name,
            "param_type": param.param_type,
            "description": param.description,
            "is_optional": param.is_optional,
            "default_value": param.default_value
        })
    
    function_data = {
        "id": function.id,
        "name": function.name,
        "signature": function.full_signature(),
        "description": function.description,
        "example_code": function.example_code,
        "is_deprecated": function.is_deprecated,
        "namespace": function.namespace.name,
        "parameters": params
    }
    
    return jsonify({"success": True, "function": function_data})