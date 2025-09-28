import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy so it can be used by the app
db = SQLAlchemy()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        # Configure the SQLite database path
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(app.instance_path, 'plant_data.sqlite')}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False, # Optional: Suppress a warning
    )

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize the db with the app
    db.init_app(app)

    # Import and register the blueprint
    from . import dashboard
    from . import auth
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(auth.bp)

    # Import models and create the database tables
    with app.app_context():
        from . import models
        db.create_all()

    # Make the dashboard the default home page
    app.add_url_rule('/', endpoint='dashboard.nuclear_dashboard')

    return app