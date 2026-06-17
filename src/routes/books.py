from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import or_

from extensions import db
from models import Book, BorrowRecord, Category
from routes.helpers import log_action, login_required, roles_required


books_bp = Blueprint("books", __name__, url_prefix="/books")


@books_bp.route("/")
@login_required
def list_books():
    search = request.args.get("search", "").strip()
    category_id = request.args.get("category_id", "").strip()

    query = Book.query
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Book.title.ilike(like), Book.author.ilike(like), Book.isbn.ilike(like)))
    if category_id:
        query = query.filter_by(category_id=int(category_id))

    books = query.order_by(Book.title.asc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template("books/list.html", books=books, categories=categories, search=search, category_id=category_id)


@books_bp.route("/add", methods=["GET", "POST"])
@roles_required("admin", "librarian")
def add_book():
    categories = Category.query.order_by(Category.name.asc()).all()

    if request.method == "POST":
        isbn = request.form.get("isbn", "").strip()
        if Book.query.filter_by(isbn=isbn).first():
            flash("A book with this ISBN already exists.", "danger")
            return redirect(url_for("books.add_book"))

        book = Book(
            title=request.form.get("title", "").strip(),
            author=request.form.get("author", "").strip(),
            isbn=isbn,
            publisher=request.form.get("publisher", "").strip(),
            year=int(request.form.get("year") or 0) or None,
            quantity=max(0, int(request.form.get("quantity") or 0)),
            description=request.form.get("description", "").strip(),
            image=request.form.get("image", "").strip(),
            category_id=int(request.form.get("category_id")),
        )
        db.session.add(book)
        db.session.commit()
        log_action(f"Added book {book.title}")
        flash("Book added.", "success")
        return redirect(url_for("books.list_books"))

    return render_template("books/form.html", book=None, categories=categories)


@books_bp.route("/edit/<int:book_id>", methods=["GET", "POST"])
@roles_required("admin", "librarian")
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    categories = Category.query.order_by(Category.name.asc()).all()

    if request.method == "POST":
        isbn = request.form.get("isbn", "").strip()
        duplicate = Book.query.filter(Book.id != book.id, Book.isbn == isbn).first()
        if duplicate:
            flash("A different book already uses this ISBN.", "danger")
            return redirect(url_for("books.edit_book", book_id=book.id))

        book.title = request.form.get("title", "").strip()
        book.author = request.form.get("author", "").strip()
        book.isbn = isbn
        book.publisher = request.form.get("publisher", "").strip()
        book.year = int(request.form.get("year") or 0) or None
        book.quantity = max(0, int(request.form.get("quantity") or 0))
        book.description = request.form.get("description", "").strip()
        book.image = request.form.get("image", "").strip()
        book.category_id = int(request.form.get("category_id"))

        db.session.commit()
        log_action(f"Updated book {book.title}")
        flash("Book updated.", "success")
        return redirect(url_for("books.list_books"))

    return render_template("books/form.html", book=book, categories=categories)


@books_bp.route("/delete/<int:book_id>", methods=["POST"])
@roles_required("admin", "librarian")
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    active = BorrowRecord.query.filter_by(book_id=book.id, status="borrowed").count()

    if active:
        flash("Cannot delete a book that is currently borrowed.", "danger")
        return redirect(url_for("books.list_books"))

    title = book.title
    db.session.delete(book)
    db.session.commit()
    log_action(f"Deleted book {title}")
    flash("Book deleted.", "success")
    return redirect(url_for("books.list_books"))