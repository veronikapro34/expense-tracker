from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Expense
from collections import defaultdict

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret-key-change-me"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expenses.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            flash("Такой логин уже занят")
            return redirect(url_for("register"))

        user = User(
            username=username,
            password=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        flash("Готово! Теперь войди")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))

        flash("Неверный логин или пароль")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    total = sum(e.amount for e in expenses)

    by_category = defaultdict(float)
    for e in expenses:
        by_category[e.category] += e.amount

    return render_template(
        "index.html",
        expenses=expenses,
        total=total,
        categories=dict(by_category)
    )


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
        except ValueError:
            flash("Сумма должна быть числом")
            return redirect(url_for("add"))

        expense = Expense(
            amount=amount,
            category=request.form["category"].strip().lower(),
            comment=request.form.get("comment", "").strip(),
            user_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("add.html")


@app.route("/delete/<int:id>")
@login_required
def delete(id):
    expense = Expense.query.get_or_404(id)
    if expense.user_id == current_user.id:
        db.session.delete(expense)
        db.session.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)