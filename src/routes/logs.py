from flask import Blueprint, render_template

from models import ActivityLog
from routes.helpers import roles_required


logs_bp = Blueprint("logs", __name__, url_prefix="/logs")


@logs_bp.route("/")
@roles_required("admin")
def logs():
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(200).all()
    return render_template("logs.html", logs=logs)