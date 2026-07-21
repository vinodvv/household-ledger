from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Transaction
from datetime import datetime, date
from sqlalchemy import extract
from constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES
import os


def create_app():
    app = Flask(__name__)
    app.secret_key = "dev-key-change-this-later"
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "ledger.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()  # Creates ledger.db and the transaction table if they don't exists

    @app.route("/")
    def dashboard():
        all_tx = Transaction.query.all()
        month_str = request.args.get("month")  # e.g. "2026-08"

        if month_str:
            year, month = map(int, month_str.split("-"))
        else:
            latest = Transaction.query.order_by(Transaction.date.desc()).first()
            today = latest.date if latest else datetime.today().date()
            year, month = today.year, today.month

        transactions = Transaction.query.filter(
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == month
        ).order_by(Transaction.date.desc()).all()

        income = sum(t.amount for t in transactions if t.type == "income")
        expense = sum(t.amount for t in transactions if t.type == "expense")

        # Category breakdown (expense only, this month)
        breakdown = {}
        for t in transactions:
            if t.type == "expense":
                breakdown[t.category] = breakdown.get(t.category, 0) + t.amount
        breakdown = dict(sorted(breakdown.items(), key=lambda x: x[1], reverse=True))

        # month-over-month trend (all months present in the data
        months_set = sorted({t.date.strftime("%Y-%m") for t in all_tx})

        current = f"{year:04d}-{month:02d}"
        idx = months_set.index(current) if current in months_set else -1
        prev_month = months_set[idx - 1] if idx > 0 else None
        next_month = months_set[idx + 1] if 0 <= idx < len(months_set) - 1 else None

        trend_income, trend_expense = [], []
        for m in months_set:
            y, mo = map(int, m.split("-"))
            trend_income.append(
                sum(t.amount for t in all_tx if t.type == "income" and t.date.year == y and t.date.month == mo)
            )
            trend_expense.append(
                sum(t.amount for t in all_tx if t.type == "expense" and t.date.year == y and t.date.month == mo)
            )
        trend_labels = [datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in months_set]

        return render_template(
            "dashboard.html",
            transactions=transactions,
            income=income, expense=expense, net=income - expense,
            month_label=datetime(year, month, 1).strftime("%B %Y"),
            months=months_set,
            prev_month=prev_month,
            next_month=next_month,
            selected_month=f"{year:04d}-{month:02d}",
            category_labels=list(breakdown.keys()),
            category_values=list(breakdown.values()),
            trend_labels=trend_labels,
            trend_income=trend_income,
            trend_expense=trend_expense,
        )

    @app.route("/add", methods=["GET", "POST"])
    def add_entry():
        if request.method == "POST":
            amount = float(request.form["amount"] or 0)
            description = request.form["description"].strip()
            if amount <= 0 or not description:
                flash("Please enter a description and an amount greater than 0.")
                return render_template(
                    "entry_form.html", entry=None, today=date.today().isoformat(),
                    expense_categories=EXPENSE_CATEGORIES, income_categories=INCOME_CATEGORIES
                )
            t = Transaction(
                type=request.form["type"],
                date=date.fromisoformat(request.form["date"]),
                amount=float(request.form["amount"]),
                description=request.form["description"],
                category=request.form["category"],
            )
            db.session.add(t)
            db.session.commit()
            flash("Entry added.")
            return redirect(url_for("dashboard", month=t.date.strftime("%Y-%m")))

        return render_template(
            "entry_form.html", entry=None, today=date.today().isoformat(),
            expense_categories=EXPENSE_CATEGORIES, income_categories=INCOME_CATEGORIES,
        )

    @app.route("/edit/<int:id>", methods=["GET", "POST"])
    def edit_entry(id):
        t = Transaction.query.get_or_404(id)
        if request.method == "POST":
            amount = float(request.form["amount"] or 0)
            description = request.form["description"].strip()
            if amount <= 0 or not description:
                flash("Please enter a description and an amount greater than 0.")
                return render_template(
                    "entry_form.html", entry=None, today=date.today().isoformat(),
                    expense_categories=EXPENSE_CATEGORIES, income_categories=INCOME_CATEGORIES
                )
            t.type = request.form["type"]
            t.date = date.fromisoformat(request.form["date"])
            t.amount = float(request.form["amount"])
            t.description = request.form["description"]
            t.category = request.form["category"]
            db.session.commit()
            flash("Entry updated.")
            return redirect(url_for("dashboard", month=t.date.strftime("%Y-%m")))

        return render_template(
            "entry_form.html", entry=t, today=date.today().isoformat(),
            expense_categories=EXPENSE_CATEGORIES, income_categories=INCOME_CATEGORIES
        )

    @app.route("/delete/<int:id>", methods=['POST'])
    def delete_entry(id):
        t = Transaction.query.get_or_404(id)
        db.session.delete(t)
        db.session.commit()
        flash("Entry deleted.")
        return redirect(url_for("dashboard"))


    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
