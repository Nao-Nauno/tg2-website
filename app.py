import os
from flask import Flask
from extensions import db, login_manager
from datetime import datetime
import asyncio
import threading
import websockets
from utils.gitlab_integration import GitLabIntegration

# Create a global gitlab integration instance
gitlab_integration = GitLabIntegration()

def start_websocket_server(host='0.0.0.0', port=8765):
    async def handle_websocket(websocket, path):
        try:
            async for message in websocket:
                # Process incoming WebSocket messages
                print(f"Received message: {message}")
                # Add your WebSocket logic here
                await websocket.send(f"Server received: {message}")
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")

    # Create a new event loop for the WebSocket server
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Create the WebSocket server
    server = websockets.serve(handle_websocket, host, port)
    
    print(f"Starting WebSocket server on {host}:{port}")
    
    # Run the server
    loop.run_until_complete(server)
    loop.run_forever()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)

    from models.user import User
    from models.post import Post
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.admin import admin_bp
    from routes.user import user_bp
    from routes.comment import comment_bp
    from routes.lua import lua_bp
    from routes.forum import forum_bp

    app.register_blueprint(lua_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(comment_bp)
    app.register_blueprint(forum_bp)

    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    @app.context_processor
    def inject_gitlab_data():
        # Get the last 4 commits instead of just the latest
        latest_commits = gitlab_integration.get_multiple_commits(4)
        project_stats = gitlab_integration.get_project_stats()
        
        return {
            'latest_commits': latest_commits,
            'project_stats': project_stats,
            'project_id': gitlab_integration.project_id,
            'gitlab_test': "GitLab integration is registered"
        }

    @app.context_processor
    def get_top_contributors():
        """Fetch top contributors from GitLab"""
        def _get_contributors():
            try:
                # This is a placeholder - you'll need to implement actual contributor fetching
                contributors = gitlab_integration.get_top_contributors()
                return contributors
            except Exception as e:
                print(f"Error fetching contributors: {str(e)}")
                return []
        return {'get_top_contributors': _get_contributors}
    
    return app

app = create_app()

# Test GitLab integration at startup
print("Testing GitLab integration...")
latest_commit = gitlab_integration.get_latest_commit()
if latest_commit:
    print(f"Latest commit: {latest_commit['title']} by {latest_commit['author_name']}")
    print(f"Full commit data: {latest_commit}")
else:
    print("Failed to get latest commit")

stats = gitlab_integration.get_project_stats()
if stats:
    print(f"Project stats: {stats['branch_count']} branches, {stats['commit_count']} commits")
else:
    print("Failed to get project stats")

if __name__ == '__main__':
    print("Starting WebSocket thread")
    websocket_thread = threading.Thread(target=start_websocket_server)
    websocket_thread.daemon = True
    websocket_thread.start()

    print("Starting Flask app")
    app.run(debug=True)