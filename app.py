from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_mail import Mail, Message
from models import db, Transaction
from datetime import datetime, date
from sqlalchemy import extract
from dotenv import load_dotenv
from constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES
import os
import calendar
import csv
import io

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.secret_key = "dev-key-change-this-later"
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")

    mail = Mail(app)

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


    @app.route("/duplicate-month", methods=["POST"])
    def duplicate_month():
        source_month = request.form["month"]  # e.g. "2026-08"
        year, month = map(int, source_month.split("-"))

        # figure out the next month/year
        if month == 12:
            target_year, target_month = year + 1, 1
        else:
            target_year, target_month = year, month + 1

        source_tx = Transaction.query.filter(
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == month
        ).all()

        if not source_tx:
            flash("No entries found in that month to duplicate.")
            return redirect(url_for("dashboard", month=source_month))

        # clamp day to last valid day of target month (e.g. Jan 31 -> Feb 28)
        last_day = calendar.monthrange(target_year, target_month)[1]

        count = 0
        for t in source_tx:
            new_day = min(t.date.day, last_day)
            db.session.add(Transaction(
                type=t.type,
                date=date(target_year, target_month, new_day),
                amount=t.amount,
                description=t.description,
                category=t.category,
            ))
            count += 1

        db.session.commit()
        target_str = f"{target_year:04d}-{target_month:02d}"
        flash(f"Duplicated {count} entries to {datetime(target_year, target_month, 1).strftime('%B %Y')}.")
        return redirect(url_for("dashboard", month=target_str))


    @app.route("/export")
    def export_csv():
        month_str = request.args.get("month")
        if month_str:
            year, month = map(int, month_str.split("-"))
        else:
            latest = Transaction.query.order_by(Transaction.date.desc()).first()
            today = latest.date if latest else date.today()
            year, month = today.year, today.month

        transactions = Transaction.query.filter(
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == month
        ).order_by(Transaction.date.asc()).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Type", "Description", "Category", "Amount"])
        for t in transactions:writer.writerow([t.date.strftime("%d-%m-%Y"), t.type, t.description, t.category, t.amount])
        month_label = datetime(year, month, 1).strftime("%Y-%m")
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=ledger_{month_label}.csv"}
        )


    @app.route("/email-report", methods=["POST"])
    def email_report():
        month_str = request.form["month"]
        year, month = map(int, month_str.split("-"))

        transactions = Transaction.query.filter(
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == month
        ).order_by(Transaction.date.asc()).all()

        if not transactions:
            flash("No entries found for that month.")
            return redirect(url_for("dashboard", month=month_str))

        income = sum(t.amount for t in transactions if t.type == "income")
        expense = sum(t.amount for t in transactions if t.type == "expense")
        month_label = datetime(year, month, 1).strftime("%B %Y")

        # build the CSV attachment
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Type", "Description", "Category", "Amount"])
        for t in transactions:
            writer.writerow([
                t.date.strftime("%d-%m-%Y"), t.type, t.description, t.category, t.amount
            ])

        recipient = os.environ.get("MAIL_RECIPIENT")
        if not recipient:
            flash("MAIL_RECIPIENT is not set -- check you .env file.")
            return redirect(url_for("dashboard", month=month_str))

        msg = Message(
            subject=f"Household Ledger - {month_label}",
            recipients=[recipient],
            body=(
                f"Report for {month_label}\n\n"
                f"Income:        Rs. {income:,.0f}\n"
                f"Expenses:    Rs. {expense:,.0f}\n"
                f"Net:              Rs. {income - expense:,.0f}\n\n"
                f"Full detail attached as CSV."
            )
        )
        msg.attach(
            filename=f"ledger_{month_str}.csv",
            content_type="text/csv",
            data=output.getvalue()
        )

        try:
            mail.send(msg)
            flash(f"Report for {month_label} emailed to {recipient}.")
        except Exception as e:
            flash(f"Failed to send email: {e}")

        return redirect(url_for("dashboard", month=month_str))


    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
