from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import or_

from extensions import db
from models import User
from routes.helpers import log_action, roles_required


users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.route("/")
@roles_required("admin")
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("users/list.html", users=users)


@users_bp.route("/add", methods=["GET", "POST"])
@roles_required("admin")
def add_user():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        role = request.form.get("role", "user")
        password = request.form.get("password", "")

        if role not in ["admin", "librarian", "user"]:
            flash("Invalid role.", "danger")
            return redirect(url_for("users.add_user"))

        if User.query.filter(or_(User.username == username, User.email == email)).first():
            flash("Username or email already exists.", "danger")
            return redirect(url_for("users.add_user"))

        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        log_action(f"Created user {username}")
        flash("User created.", "success")
        return redirect(url_for("users.list_users"))

    return render_template("users/form.html", user=None)


@users_bp.route("/edit/<int:user_id>", methods=["GET", "POST"])
@roles_required("admin")
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        role = request.form.get("role", "user")
        password = request.form.get("password", "")

        duplicate = User.query.filter(
            User.id != user.id,
            or_(User.username == username, User.email == email),
        ).first()
        if duplicate:
            flash("Username or email already exists.", "danger")
            return redirect(url_for("users.edit_user", user_id=user.id))

        user.username = username
        user.email = email
        user.role = role
        if password:
            user.set_password(password)

        db.session.commit()
        log_action(f"Updated user {user.username}")
        flash("User updated.", "success")
        return redirect(url_for("users.list_users"))

    return render_template("users/form.html", user=user)


@users_bp.route("/delete/<int:user_id>", methods=["POST"])
@roles_required("admin")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.username == "admin":
        flash("The default admin account cannot be deleted.", "danger")
        return redirect(url_for("users.list_users"))

    db.session.delete(user)
    db.session.commit()
    log_action(f"Deleted user {user.username}")
    flash("User deleted.", "success")
    return redirect(url_for("users.list_users"))