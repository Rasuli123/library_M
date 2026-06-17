from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from extensions import db
from models import SystemSetting, User
from routes.helpers import clear_jwt_cookie, create_jwt_for_user, current_user, log_action, set_jwt_cookie


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            token = create_jwt_for_user(user)
            session.clear()
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            if user.username == "admin" and SystemSetting.get_bool("default_admin_hint_visible", True):
                SystemSetting.set_bool("default_admin_hint_visible", False)
                db.session.flush()
            log_action(f"{user.username} logged in", user_id=user.id)
            flash("Login successful.", "success")
            response = redirect(url_for("dashboard.dashboard"))
            set_jwt_cookie(response, token)
            return response

        flash("Invalid username or password.", "danger")

    show_default_admin_hint = SystemSetting.get_bool("default_admin_hint_visible", True)
    return render_template("login.html", show_default_admin_hint=show_default_admin_hint)


@auth_bp.route("/logout")
def logout():
    user = current_user()
    username = user.username if user else session.get("username", "User")
    log_action(f"{username} logged out", user_id=user.id if user else None)
    session.clear()
    flash("You have been logged out.", "info")
    response = redirect(url_for("auth.login"))
    clear_jwt_cookie(response)
    return response