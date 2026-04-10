from flask import Flask
from config import Config
from shop.extensions import db, migrate, jwt, bcrypt, mail

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)

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

    @app.route('/')
    def home():
        return {"message": "E-Commerce API is Running!"}

    return app