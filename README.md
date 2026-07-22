# Household Ledger

A simple Flask + SQLite web app for tracking monthly household income and expenses — data entry, storage, and at-a-glance reporting.

## Features

- Add, edit, and delete income and expense entries
- Monthly dashboard with income, expense, and net totals
- Category breakdown chart (where your money went this month)
- Income vs. expense trend chart across all months
- Month picker with prev/next navigation
- "Duplicate to next month" — copy a month's recurring entries (SIPs, rent, EMIs, etc.) forward in one click
- Data persists in a local SQLite database

## Tech stack

- [Flask](https://flask.palletsprojects.com/) — web framework
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) — ORM / database
- [Chart.js](https://www.chartjs.org/) — charts (loaded via CDN)
- SQLite — storage

## Project structure

```
household-ledger/
├── app.py              # Flask app factory, routes
├── models.py            # SQLAlchemy Transaction model
├── constants.py          # Expense/income category lists
├── seed.py              # One-off script to load sample/starter data
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   └── entry_form.html
├── static/
│   └── style.css
├── requirements.txt
└── .gitignore
```

## Setup (local development)

1. Clone the repo and enter the folder:
   ```bash
   git clone https://github.com/vinodvv/household-ledger.git
   cd household-ledger
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the app:
   ```bash
   python app.py
   ```
   This creates `ledger.db` automatically on first run.

5. Visit **http://127.0.0.1:5000** in your browser.

### Optional: load starter data

```bash
python seed.py
```

## Deployment

This app is set up to deploy on [PythonAnywhere](https://www.pythonanywhere.com) using a manually-configured web app pointed at a virtualenv, with the WSGI file importing `app` from `app.py`. After every `git pull` on the server, remember to:

```bash
workon ledger-venv
pip install -r requirements.txt   # if dependencies changed
```

...then reload the web app from the PythonAnywhere **Web** tab for changes to take effect.

## License

See [LICENSE](LICENSE).