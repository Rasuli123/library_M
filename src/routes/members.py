from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import Member
from routes.helpers import log_action, roles_required


members_bp = Blueprint("members", __name__, url_prefix="/members")


@members_bp.route("/")
@roles_required("admin", "librarian")
def list_members():
    search = request.args.get("search", "").strip()
    query = Member.query
    if search:
        query = query.filter(Member.name.ilike(f"%{search}%"))
    members = query.order_by(Member.name.asc()).all()
    return render_template("members/list.html", members=members, search=search)


@members_bp.route("/add", methods=["GET", "POST"])
@roles_required("admin", "librarian")
def add_member():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if Member.query.filter_by(email=email).first():
            flash("A member with this email already exists.", "danger")
            return redirect(url_for("members.add_member"))

        member = Member(
            name=request.form.get("name", "").strip(),
            email=email,
            phone=request.form.get("phone", "").strip(),
        )
        db.session.add(member)
        db.session.commit()
        log_action(f"Registered member {member.name}")
        flash("Member registered.", "success")
        return redirect(url_for("members.list_members"))

    return render_template("members/form.html", member=None)


@members_bp.route("/edit/<int:member_id>", methods=["GET", "POST"])
@roles_required("admin", "librarian")
def edit_member(member_id):
    member = Member.query.get_or_404(member_id)

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        duplicate = Member.query.filter(Member.id != member.id, Member.email == email).first()
        if duplicate:
            flash("A different member already uses this email.", "danger")
            return redirect(url_for("members.edit_member", member_id=member.id))

        member.name = request.form.get("name", "").strip()
        member.email = email
        member.phone = request.form.get("phone", "").strip()
        db.session.commit()
        log_action(f"Updated member {member.name}")
        flash("Member updated.", "success")
        return redirect(url_for("members.list_members"))

    return render_template("members/form.html", member=member)


@members_bp.route("/delete/<int:member_id>", methods=["POST"])
@roles_required("admin", "librarian")
def delete_member(member_id):
    member = Member.query.get_or_404(member_id)
    if any(record.status == "borrowed" for record in member.borrow_records):
        flash("Cannot delete a member with active borrowed books.", "danger")
        return redirect(url_for("members.list_members"))

    name = member.name
    db.session.delete(member)
    db.session.commit()
    log_action(f"Deleted member {name}")
    flash("Member deleted.", "success")
    return redirect(url_for("members.list_members"))