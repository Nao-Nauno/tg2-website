import asyncio
import json
import logging
from datetime import datetime

import websockets
from flask_login import current_user

# Store active connections
connected_clients = {}
# Map script IDs to sets of connected user IDs
script_collaborators = {}

async def register(websocket, script_id, user_id):
    """Register a new client websocket connection"""
    if script_id not in connected_clients:
        connected_clients[script_id] = {}
    
    connected_clients[script_id][user_id] = websocket
    
    # Notify other users about the new connection
    if script_id not in script_collaborators:
        script_collaborators[script_id] = set()
    
    script_collaborators[script_id].add(user_id)
    
    # Send notification to all other clients connected to this script
    await notify_collaborator_status(script_id, user_id, "online")

async def unregister(script_id, user_id):
    """Unregister a client websocket connection"""
    if script_id in connected_clients and user_id in connected_clients[script_id]:
        del connected_clients[script_id][user_id]
        
        # Clean up empty dictionaries
        if not connected_clients[script_id]:
            del connected_clients[script_id]
    
    if script_id in script_collaborators and user_id in script_collaborators[script_id]:
        script_collaborators[script_id].remove(user_id)
        
        # Clean up empty sets
        if not script_collaborators[script_id]:
            del script_collaborators[script_id]
    
    # Notify other clients about the disconnection
    await notify_collaborator_status(script_id, user_id, "offline")

async def notify_collaborator_status(script_id, user_id, status):
    """Notify all clients of a collaborator's status change"""
    if script_id in connected_clients:
        message = json.dumps({
            "type": "collaborator_status",
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        for client_id, websocket in connected_clients[script_id].items():
            if client_id != user_id:  # Don't send to the user themselves
                try:
                    await websocket.send(message)
                except websockets.exceptions.ConnectionClosed:
                    logging.warning(f"Failed to send to client {client_id}, connection closed")

async def broadcast_changes(script_id, user_id, changes):
    """Broadcast script changes to all connected clients"""
    if script_id in connected_clients:
        message = json.dumps({
            "type": "script_change",
            "user_id": user_id,
            "changes": changes,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        for client_id, websocket in connected_clients[script_id].items():
            if client_id != user_id:  # Don't send back to the originator
                try:
                    await websocket.send(message)
                except websockets.exceptions.ConnectionClosed:
                    logging.warning(f"Failed to send to client {client_id}, connection closed")

async def handle_websocket(websocket, path):
    """Handle a websocket connection"""
    # Extract script_id from path (e.g., '/ws/script/123')
    parts = path.strip('/').split('/')
    if len(parts) != 3 or parts[0] != 'ws' or parts[1] != 'script':
        logging.error(f"Invalid WebSocket path: {path}")
        return
    
    try:
        script_id = int(parts[2])
    except ValueError:
        logging.error(f"Invalid script ID in WebSocket path: {path}")
        return
    
    # Get user_id from initial message
    try:
        initial_message = await websocket.recv()
        data = json.loads(initial_message)
        
        if 'user_id' not in data:
            logging.error("No user_id provided in initial WebSocket message")
            return
            
        user_id = data['user_id']
        
    except (websockets.exceptions.ConnectionClosed, json.JSONDecodeError) as e:
        logging.error(f"Error during WebSocket handshake: {e}")
        return
    
    await register(websocket, script_id, user_id)
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                
                if data['type'] == 'script_change':
                    await broadcast_changes(script_id, user_id, data['changes'])
                # Add more message types as needed
                
            except json.JSONDecodeError:
                logging.error(f"Invalid JSON received: {message}")
    finally:
        await unregister(script_id, user_id)
        
def start_websocket_server(host='localhost', port=8765):
    """Start the WebSocket server"""
    print(f"Starting WebSocket server on {host}:{port}")
    logging.info(f"Starting WebSocket server on {host}:{port}")
    return websockets.serve(handle_websocket, host, port)