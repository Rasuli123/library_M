from .auth import auth_bp
from .books import books_bp
from .borrow import borrow_bp
from .database import database_bp
from .dashboard import dashboard_bp
from .logs import logs_bp
from .members import members_bp
from .statistics import statistics_bp
from .users import users_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(borrow_bp)
    app.register_blueprint(statistics_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(database_bp)