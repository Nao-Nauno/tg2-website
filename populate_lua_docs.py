# reset_and_load_lua_docs.py
import json
from flask import Flask
from extensions import db

from app import create_app

app = create_app()

with app.app_context():
    from models.lua_docs import LuaNamespace, LuaFunction, LuaParameter
    
    # First, wipe all existing Lua documentation
    print("Wiping existing Lua documentation...")
    
    # Delete parameters first (due to foreign key constraints)
    LuaParameter.query.delete()
    
    # Delete functions next
    LuaFunction.query.delete()
    
    # Delete namespaces last
    LuaNamespace.query.delete()
    
    db.session.commit()
    print("All existing Lua documentation deleted.")
    
    # Load functions from JSON
    json_file_path = 'lua_functions.json'  # Update this path if needed
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_file_path} not found!")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: {json_file_path} contains invalid JSON!")
        exit(1)
    
    print(f"Loading documentation from {json_file_path}...")
    
    # Create namespaces
    namespaces = {}
    for ns_name, ns_data in data.items():
        ns = LuaNamespace(name=ns_name, description=ns_data.get('description', ''))
        db.session.add(ns)
        namespaces[ns_name] = ns
    
    db.session.flush()
    print(f"Created {len(namespaces)} namespaces.")
    
    # Add functions
    function_count = 0
    parameter_count = 0
    
    for ns_name, ns_data in data.items():
        for func_data in ns_data.get('functions', []):
            func = LuaFunction(
                name=func_data['name'],
                signature=func_data.get('signature', '()'),
                description=func_data.get('description', ''),
                example_code=func_data.get('example_code', ''),
                namespace=namespaces[ns_name],
                added_in_version=func_data.get('added_in_version', ''),
                is_deprecated=func_data.get('is_deprecated', False),
                deprecated_message=func_data.get('deprecated_message', '')
            )
            
            db.session.add(func)
            db.session.flush()
            function_count += 1
            
            # Add parameters
            for param_data in func_data.get('parameters', []):
                param = LuaParameter(
                    name=param_data['name'],
                    param_type=param_data['param_type'],
                    description=param_data.get('description', ''),
                    is_optional=param_data.get('is_optional', False),
                    default_value=param_data.get('default_value', ''),
                    function=func
                )
                db.session.add(param)
                parameter_count += 1
    
    db.session.commit()
    print(f"Added {function_count} functions with {parameter_count} parameters.")
    print("Lua documentation loaded successfully!")