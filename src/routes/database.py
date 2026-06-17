from flask import Blueprint, render_template
from sqlalchemy import inspect

from extensions import db
from models import ALL_MODELS
from routes.helpers import roles_required


database_bp = Blueprint("database", __name__, url_prefix="/admin/database")


def _safe_database_url():
    return db.engine.url.render_as_string(hide_password=True)


@database_bp.route("/")
@roles_required("admin")
def database_status():
    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())
    table_statuses = []
    total_rows = 0

    for model in ALL_MODELS:
        table_name = model.__tablename__
        exists = table_name in existing_tables
        columns = []
        row_count = None
        error = None

        if exists:
            columns = [column["name"] for column in inspector.get_columns(table_name)]
            try:
                row_count = db.session.query(model).count()
                total_rows += row_count
            except Exception as exc:
                db.session.rollback()
                error = str(exc)

        table_statuses.append(
            {
                "name": table_name,
                "exists": exists,
                "columns": columns,
                "row_count": row_count,
                "error": error,
            }
        )

    return render_template(
        "database/status.html",
        database_url=_safe_database_url(),
        dialect=db.engine.dialect.name,
        driver=db.engine.driver,
        table_statuses=table_statuses,
        total_rows=total_rows,
        all_ready=all(table["exists"] and not table["error"] for table in table_statuses),
    )