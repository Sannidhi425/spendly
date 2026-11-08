# Spendly

A simple expense tracker web app. Create an account, log your daily expenses by category and see your total spending for the current month.

## Features

- User signup, login and logout (passwords are hashed, never stored as plain text)
- Add expenses with title, amount, category and date
- View all your expenses, newest first
- Edit and delete an expense (a user can only change their own expenses)
- Monthly spending total on the dashboard
- Category-wise spending chart.

## Tech Stack

- Python, Flask
- SQLite
- HTML, CSS (Jinja2 templates)

## Run Locally

1. Clone the repo and open the folder

```
git clone https://github.com/Sannidhi425/spendly.git
cd spendly
```

2. Create and activate a virtual environment

```
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies

```
pip install -r requirements.txt
```

4. Start the app

```
python app.py
```

5. Open `http://127.0.0.1:5001` in your browser

The SQLite database (`spendly.db`) is created automatically on first run.

## Future Improvements

- Budget alerts
- CSV export
- Spending insights