from flask import Flask
import os
from extensions import db, login_manager
from datetime import datetime
import asyncio
import threading

def start_websocket_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    from websocket import start_websocket_server
    start_server = start_websocket_server(host='0.0.0.0')
    
    print("Starting WebSocket server loop")
    loop.run_until_complete(start_server)
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
        return User.query.get(int(user_id))

    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.admin import admin_bp
    from routes.user import user_bp
    from routes.comment import comment_bp
    from routes.lua import lua_bp

    app.register_blueprint(lua_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(comment_bp)

    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    return app

app = create_app()

if __name__ == '__main__':
    print("Starting WebSocket thread")
    websocket_thread = threading.Thread(target=start_websocket_thread)
    websocket_thread.daemon = True
    websocket_thread.start()

    print("Starting Flask app")
    app.run(debug=True)