from datetime import date
from app import create_app
from models import db, Transaction

app = create_app()

expenses = [
    (date(2026, 8, 1), 19306, "Axis Bank CC dues", "Credit Card Dues"),
    (date(2026, 8, 3), 500, "MF SIP Quant", "Investment"),
    (date(2026, 8, 3), 6100, "RD DOP Bank", "Savings"),
    (date(2026, 8, 3), 689, "APY - Jayasree", "Savings"),
    (date(2026, 8, 5), 500, "MF SIP Silver Groww", "Investment"),
    (date(2026, 8, 5), 500, "MF SIP Gold Groww", "Investment"),
    (date(2026, 8, 5), 500, "MF SIP SBI", "Investment"),
    (date(2026, 8, 5), 6000, "Maintenance", "Living Expense"),
    (date(2026, 8, 5), 4000, "Amazon Paylater", "Paylater"),
    (date(2026, 8, 5), 8150, "MF SIP Jayasree", "Investment"),
    (date(2026, 8, 5), 400, "Paper", "Subscription"),
    (date(2026, 8, 5), 32233, "Home Loan - LIC", "Home Loan"),
    (date(2026, 8, 7), 500, "MF SIP Axis Bank", "Investment"),
    (date(2026, 8, 8), 10000, "HDFC Bank CC dues Jayasree", "Credit Card Dues"),
    (date(2026, 8, 10), 100, "MF SIP Silver Groww", "Investment"),
    (date(2026, 8, 10), 200, "MF SIP ICICI Groww", "Investment"),
    (date(2026, 8, 10), 100, "MF SIP JM Groww", "Investment"),
    (date(2026, 8, 10), 100, "MF SIP Kotak Groww", "Investment"),
    (date(2026, 8, 10), 200, "MF SIP Nippon Groww", "Investment"),
    (date(2026, 8, 10), 500, "MF SIP Invesco", "Investment"),
    (date(2026, 8, 10), 200, "MF SIP Axis Bank", "Investment"),
    (date(2026, 8, 10), 22000, "Rent", "Living Expense"),
    (date(2026, 8, 10), 2000, "SI - SSA Anagha", "Savings"),
    (date(2026, 8, 10), 2000, "SI - SSA Advika", "Savings"),
    (date(2026, 8, 10), 2000, "SI - PPF Jayasree", "Savings"),
    (date(2026, 8, 10), 10000, "School Fees - Advika", "Education"),
    (date(2026, 8, 10), 10000, "School Fees - Anagha", "Education"),
    (date(2026, 8, 10), 500, "Car cleaning", "Utilities"),
    (date(2026, 8, 11), 100, "MF SIP Nippon", "Investment"),
    (date(2026, 8, 14), 4750, "KSFE Chitty", "Savings"),
    (date(2026, 8, 15), 8000, "Groceries", "Living Expense"),
    (date(2026, 8, 15), 2500, "Fuel", "Transportation"),
    (date(2026, 8, 16), 219, "iCloud subscription", "Subscription"),
    (date(2026, 8, 18), 9000, "Axis Bank CC dues Jayasree", "Credit Card Dues"),
    (date(2026, 8, 19), 169, "Kindle subscription", "Subscription"),
    (date(2026, 8, 20), 39200, "Gokulam Chitty", "Savings"),
    (date(2026, 8, 20), 2000, "Misc Expense", "Misc"),
    (date(2026, 8, 28), 4000, "Amex CC", "Credit Card Dues"),
    (date(2026, 8, 20), 4000, "KSEB Bill Kanjikode", "Utilities"),
    (date(2026, 8, 20), 2000, "KWA Bill Kanjikode", "Utilities"),
]

income = [
    (date(2026, 7, 31), 35845, "Pension", "Pension"),
    (date(2026, 8, 5), 12500, "Rent Ground Floor", "Kanjikode property"),
    (date(2026, 8, 5), 9000, "Rent First Floor", "Kanjikode property"),
    (date(2026, 8, 10), 10500, "Rent Second Floor", "Kanjikode property"),
    (date(2026, 8, 10), 100000, "Fund Transfer", "Jayasree"),
]

with app.app_context():
    if Transaction.query.count() > 0:
        print(f"Database already has {Transaction.query.count()} entries.")
        confirm = input("Add seed data anyway? This won't delete existing entries. (y/n): ")
        if confirm.lower() != "y":
            print("Cancelled.")
            exit()

    for d, amt, desc, cat in expenses:
        db.session.add(Transaction(type="expense", date=d, amount=amt, description=desc, category=cat))

    for d, amt, desc, cat in income:
        db.session.add(Transaction(type="income", date=d, amount=amt, description=desc, category=cat))

    db.session.commit()
    print(f"Seeded {len(expenses)} expenses and {len(income)} income entries.")
