import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, url_for
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import ALL_MODELS, ActivityLog, Category, SystemSetting, User
from routes import register_blueprints


load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")
    # Require DATABASE_URL (e.g. Supabase Postgres connection string).
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Set it to your Supabase Postgres connection string."
        )
    if "YOUR-PASSWORD" in database_url or "<password>" in database_url:
        raise RuntimeError(
            "DATABASE_URL contains a placeholder password. Set your real Supabase password in .env."
        )
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", app.config["SECRET_KEY"])
    app.config["JWT_EXPIRATION_HOURS"] = int(os.environ.get("JWT_EXPIRATION_HOURS", "8"))
    app.config["JWT_COOKIE_NAME"] = os.environ.get("JWT_COOKIE_NAME", "library_auth_token")
    app.config["JWT_COOKIE_SECURE"] = os.environ.get("JWT_COOKIE_SECURE", "false").lower() == "true"

    db.init_app(app)
    register_blueprints(app)

    with app.app_context():
        initialize_database(app)
        create_default_data()

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    return app


def initialize_database(app):
    """Create and verify every SQLAlchemy table in the connected database."""
    try:
        db.create_all()

        inspector = inspect(db.engine)
        expected_tables = [model.__tablename__ for model in ALL_MODELS]
        existing_tables = set(inspector.get_table_names())
        missing_tables = [table for table in expected_tables if table not in existing_tables]
    except SQLAlchemyError as exc:
        raise RuntimeError(
            "Could not connect to the configured database. Check that DATABASE_URL is the exact "
            "Supabase Postgres connection string from the Connect panel, that the project is active, "
            "and that your network can reach the database host."
        ) from exc

    if missing_tables:
        raise RuntimeError(
            "Database setup did not create these tables: "
            + ", ".join(missing_tables)
            + ". Check that DATABASE_URL points to Supabase Postgres and the user can create tables."
        )

    app.logger.info("Database ready. Verified tables: %s", ", ".join(expected_tables))


def create_default_data():
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(username="admin", email="admin@example.com", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)

    for name in ["Programming", "Science", "History"]:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))

    if not SystemSetting.query.get("default_admin_hint_visible"):
        admin_was_used = ActivityLog.query.filter(ActivityLog.action.ilike("%admin logged in%")).first()
        SystemSetting.set_bool("default_admin_hint_visible", not bool(admin_was_used))

    db.session.commit()


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)