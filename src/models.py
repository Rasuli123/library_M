from datetime import datetime, date

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    logs = db.relationship("ActivityLog", back_populates="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_librarian(self):
        return self.role == "librarian"


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    books = db.relationship("Book", back_populates="category", lazy=True)


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    isbn = db.Column(db.String(50), unique=True, nullable=False)
    publisher = db.Column(db.String(150))
    year = db.Column(db.Integer)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    category = db.relationship("Category", back_populates="books")
    borrow_records = db.relationship("BorrowRecord", back_populates="book", lazy=True)

    @property
    def active_borrow_count(self):
        return BorrowRecord.query.filter_by(book_id=self.id, status="borrowed").count()

    @property
    def can_delete(self):
        return self.active_borrow_count == 0


class Member(db.Model):
    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    registration_date = db.Column(db.Date, default=date.today)

    borrow_records = db.relationship("BorrowRecord", back_populates="member", lazy=True)


class BorrowRecord(db.Model):
    __tablename__ = "borrow_records"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    borrow_date = db.Column(db.Date, default=date.today, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    status = db.Column(db.String(20), default="borrowed", nullable=False)

    book = db.relationship("Book", back_populates="borrow_records")
    member = db.relationship("Member", back_populates="borrow_records")

    @property
    def is_overdue(self):
        return self.status == "borrowed" and self.return_date is None and date.today() > self.due_date


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="logs")


class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_bool(cls, key, default=False):
        setting = cls.query.get(key)
        if not setting:
            return default
        return setting.value == "true"

    @classmethod
    def set_bool(cls, key, value):
        setting = cls.query.get(key)
        if not setting:
            setting = cls(key=key, value="true" if value else "false")
            db.session.add(setting)
        else:
            setting.value = "true" if value else "false"


ALL_MODELS = [
    User,
    Category,
    Book,
    Member,
    BorrowRecord,
    ActivityLog,
    SystemSetting,
]