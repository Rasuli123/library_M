from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import abort, current_app, flash, redirect, request, session, url_for

from extensions import db
from models import ActivityLog, User


def create_jwt_for_user(user):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(hours=current_app.config["JWT_EXPIRATION_HOURS"]),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def set_jwt_cookie(response, token):
    max_age = current_app.config["JWT_EXPIRATION_HOURS"] * 3600
    response.set_cookie(
        current_app.config["JWT_COOKIE_NAME"],
        token,
        max_age=max_age,
        httponly=True,
        secure=current_app.config["JWT_COOKIE_SECURE"],
        samesite="Lax",
    )


def clear_jwt_cookie(response):
    response.delete_cookie(current_app.config["JWT_COOKIE_NAME"])


def _sync_session_user(user):
    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role


def current_user():
    token = request.cookies.get(current_app.config["JWT_COOKIE_NAME"])
    if not token:
        return None

    try:
        payload = jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None

    user = db.session.get(User, user_id)
    if user:
        _sync_session_user(user)
    return user


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user():
            session.clear()
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapper


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                session.clear()
                flash("Please login first.", "warning")
                return redirect(url_for("auth.login"))
            if user.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapper

    return decorator


def log_action(action, user_id=None):
    if user_id is None:
        user = current_user()
        user_id = user.id if user else None
    db.session.add(ActivityLog(user_id=user_id, action=action))
    db.session.commit()