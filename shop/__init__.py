from flask import Flask , jsonify
from config import Config
from shop.extensions import db, migrate, jwt, bcrypt, mail, limiter



def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)


    # ===============================================================================================
    import logging
    from logging.handlers import RotatingFileHandler
    import os

    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # maxBytes=1024000 matlab 1MB ki file banegi, uske baad nayi file ban jayegi (backupCount=10)
    file_handler = RotatingFileHandler('logs/ecom_app.log', maxBytes=1024000, backupCount=10, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('E-Commerce API Startup! 🚀')
# ===============================================================================================



    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    limiter.init_app(app) 

    from shop import models

    # Blueprints register karna
    from shop.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from shop.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    from shop.seller import seller_bp
    app.register_blueprint(seller_bp, url_prefix='/api/seller')

    from shop.user import user_bp
    app.register_blueprint(user_bp, url_prefix='/api/user')



    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            "success": False,
            "message": f"Too many requests! {e.description}"
        }), 429


    @app.route('/')
    def home():
        return {"message": "E-Commerce API is Running!"}

    return app