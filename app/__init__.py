from flask import Flask

def create_app(config_name="development"):
    app = Flask(__name__)
    app.debug = True

    # Load configuration based on the provided config_name
    # app.config.from_object(f"config.{config_name}")

    # Initialize any extensions you might be using (e.g., SQLAlchemy, Flask-WTF, etc.)
    # db.init_app(app)
    # csrf.init_app(app)

    # Register blueprints
    from .routes.test import test_bp
    app.register_blueprint(test_bp)

    # Other application setup and configuration

    return app