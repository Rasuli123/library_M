from collections import Counter, defaultdict

from flask import Blueprint, render_template

from models import Book, BorrowRecord, Category
from routes.helpers import login_required


statistics_bp = Blueprint("statistics", __name__, url_prefix="/statistics")


@statistics_bp.route("/")
@login_required
def statistics():
    categories = Category.query.order_by(Category.name.asc()).all()
    category_labels = [category.name for category in categories]
    category_counts = [Book.query.filter_by(category_id=category.id).count() for category in categories]

    borrow_records = BorrowRecord.query.all()
    borrowed_counter = Counter(record.book.title for record in borrow_records if record.book)
    most_borrowed = borrowed_counter.most_common(5)

    monthly = defaultdict(int)
    for record in borrow_records:
        monthly[record.borrow_date.strftime("%Y-%m")] += 1
    month_labels = sorted(monthly.keys())
    month_counts = [monthly[month] for month in month_labels]

    return render_template(
        "statistics.html",
        category_labels=category_labels,
        category_counts=category_counts,
        most_borrowed_labels=[item[0] for item in most_borrowed],
        most_borrowed_counts=[item[1] for item in most_borrowed],
        month_labels=month_labels,
        month_counts=month_counts,
    )