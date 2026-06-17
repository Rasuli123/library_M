from datetime import date, timedelta

from flask import Blueprint, render_template

from models import Book, BorrowRecord, Member
from routes.helpers import login_required


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    total_books = Book.query.count()
    available_books = sum(book.quantity for book in Book.query.all())
    borrowed_books = BorrowRecord.query.filter_by(status="borrowed").count()
    total_members = Member.query.count()
    overdue_books = BorrowRecord.query.filter(
        BorrowRecord.status == "borrowed",
        BorrowRecord.return_date.is_(None),
        BorrowRecord.due_date < date.today(),
    ).count()

    recent_records = BorrowRecord.query.order_by(BorrowRecord.id.desc()).limit(6).all()
    due_soon_records = (
        BorrowRecord.query.filter(
            BorrowRecord.status == "borrowed",
            BorrowRecord.return_date.is_(None),
            BorrowRecord.due_date <= date.today() + timedelta(days=7),
        )
        .order_by(BorrowRecord.due_date.asc())
        .limit(5)
        .all()
    )
    low_stock_books = (
        Book.query.filter(Book.quantity <= 2)
        .order_by(Book.quantity.asc(), Book.title.asc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard.html",
        total_books=total_books,
        available_books=available_books,
        borrowed_books=borrowed_books,
        total_members=total_members,
        overdue_books=overdue_books,
        recent_records=recent_records,
        due_soon_records=due_soon_records,
        low_stock_books=low_stock_books,
    )