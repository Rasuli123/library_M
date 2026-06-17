from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import Book, BorrowRecord, Member
from routes.helpers import current_user, log_action, login_required, roles_required


borrow_bp = Blueprint("borrow", __name__)


@borrow_bp.route("/borrow", methods=["GET", "POST"])
@roles_required("admin", "librarian")
def borrow_book():
    books = Book.query.filter(Book.quantity > 0).order_by(Book.title.asc()).all()
    members = Member.query.order_by(Member.name.asc()).all()

    if request.method == "POST":
        book = Book.query.get_or_404(int(request.form.get("book_id")))
        member = Member.query.get_or_404(int(request.form.get("member_id")))
        days = int(request.form.get("days") or 14)

        if book.quantity <= 0:
            flash("This book is not available.", "danger")
            return redirect(url_for("borrow.borrow_book"))

        record = BorrowRecord(
            book_id=book.id,
            member_id=member.id,
            borrow_date=date.today(),
            due_date=date.today() + timedelta(days=days),
            status="borrowed",
        )
        book.quantity -= 1
        db.session.add(record)
        db.session.commit()
        log_action(f"{member.name} borrowed {book.title}")
        flash("Book borrowed successfully.", "success")
        return redirect(url_for("borrow.return_book"))

    return render_template("borrow/borrow.html", books=books, members=members)


@borrow_bp.route("/return", methods=["GET", "POST"])
@roles_required("admin", "librarian")
def return_book():
    records = BorrowRecord.query.filter_by(status="borrowed").order_by(BorrowRecord.due_date.asc()).all()

    if request.method == "POST":
        record = BorrowRecord.query.get_or_404(int(request.form.get("record_id")))

        if record.status != "borrowed":
            flash("This record is already returned.", "warning")
            return redirect(url_for("borrow.return_book"))

        record.status = "returned"
        record.return_date = date.today()
        record.book.quantity += 1
        db.session.commit()
        log_action(f"{record.member.name} returned {record.book.title}")
        flash("Book returned successfully.", "success")
        return redirect(url_for("borrow.return_book"))

    return render_template("borrow/return.html", records=records)


@borrow_bp.route("/history")
@login_required
def history():
    user = current_user()

    if user.role in ["admin", "librarian"]:
        records = BorrowRecord.query.order_by(BorrowRecord.borrow_date.desc()).all()
        owner_note = "All borrowing records"
    else:
        member = Member.query.filter_by(email=user.email).first()
        records = []
        if member:
            records = (
                BorrowRecord.query.filter_by(member_id=member.id)
                .order_by(BorrowRecord.borrow_date.desc())
                .all()
            )
        owner_note = "Your borrowing records"

    return render_template("borrow/history.html", records=records, owner_note=owner_note)