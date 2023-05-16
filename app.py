import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Query database for current user id from portfolio table
    df = db.execute("SELECT * FROM portfolio WHERE user_id = ?", session["user_id"])

    # Query database for current user id from users table
    rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

    # Get cash balance
    cash = rows[0]["cash"]

    # Track total value of stocks owned
    sum = 0

    # Display all stocks data
    for row in df:

        # Look up for the stock quote to get most up-to-date data
        stock = lookup(row["stock_symbol"])

        # Get the name of the stock
        row["stock_name"] = stock["name"]

        # Get the latest price
        row["stock_price"] = stock["price"]

        # Calculate the total value with the lastest price
        row["total_value"] = row["stock_price"] * row["stock_amount"]

        # Calculate total stock value
        sum += row["total_value"]

        # Format USD
        row["stock_price"] = usd(row["stock_price"])
        row["total_value"] = usd(row["total_value"])

    # Render index template to display stock portfolio data
    return render_template("index.html", df=df, cash=usd(cash), sum=usd(sum), total=usd(sum + cash))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure stock symbol was submitted
        if not request.form.get("symbol"):
            return apology("must provide stock symbol", 400)

        # Ensure number of shares was submitted
        elif not request.form.get("shares"):
            return apology("must provide number of shares", 400)

        # Look up the stock symbol
        stock = lookup(request.form.get("symbol"))

        # Validate symbol
        if stock is None:
            return apology("invalid stock symbol", 400)

        # Validate number of shares
        if not (request.form.get("shares")).isdigit():
            return apology("invalid number of shares", 400)

        # Get number of shares
        shares = int(request.form.get("shares"))

        # Validate transactions
        # Query database for current user id from users table
        row = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # Get the amount of cash user have
        cash = row[0]["cash"]

        # Calculate the amount of transaction
        purchase = stock["price"] * shares

        # Calculate the balance after purchased the stocks
        balance = cash - purchase

        # Check the validity of the fund
        if balance < 0:
            return apology("insufficient funds", 403)

        # Update cash balance of user after transaction
        db.execute("UPDATE users SET cash = ? WHERE id = ?", balance, session["user_id"])

        # Update transaction to the history table
        db.execute("INSERT INTO history (user_id, stock_symbol, stock_amount, stock_price, total_value, method) VALUES (?, ?, ?, ?, ?, ?)",
                   session["user_id"], stock["symbol"], shares, stock["price"], purchase, "Buy")

        # Update shares in portfolio table
        # Check whether the user had that stock in portfolio
        # If the user don't have any in portfolio, insert into the portfolio table
        if len(db.execute("SELECT * FROM portfolio WHERE user_id = ? AND stock_symbol = ?", session["user_id"], stock["symbol"])) == 0:
            db.execute("INSERT INTO portfolio (user_id, stock_symbol, stock_amount, stock_name, stock_price, total_value) VALUES (?, ?, ?, ?, ?, ?)",
                       session["user_id"], stock["symbol"], shares, stock["name"], stock["price"], purchase)

        # If the user already had, update the amount of shares to the portfolio table
        else:

            # Query database for current user id with the stock symbol from portfolio table
            rows = db.execute("SELECT * FROM portfolio WHERE user_id = ? AND stock_symbol = ?", session["user_id"], stock["symbol"])

            # Get amount of shares the user already had in portfolio
            previous_shares_amount = rows[0]["stock_amount"]

            # Calculate new amount of shares after the transaction
            current_shares_amount = previous_shares_amount + shares

            # Update new amount of shares in portfolio table
            db.execute("UPDATE portfolio SET stock_amount = ? WHERE user_id = ? AND stock_symbol = ?",
                       current_shares_amount, session["user_id"], stock["symbol"])

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Render buy template
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Query all database for current user id from history table
    history = db.execute("SELECT * FROM history WHERE user_id = ?", session["user_id"])

    # Render history template
    return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Render login template
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("must provide stock symbol", 400)

        # Look up the stock symbol
        stock = lookup(request.form.get("symbol"))

        # Validate symbol
        if stock is None:
            return apology("invalid stock symbol", 400)

        # Render quoted template to display stock quote
        return render_template("quoted.html", name=stock["name"], symbol=stock["symbol"], price=usd(stock["price"]))

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Render quote template
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure the password is match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password not match", 400)

        # Ensure username not exists
        if len(db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))) != 0:
            return apology("invalid username", 400)

        # Get username
        username = request.form.get("username")

        # Get the password hashed by encryption function
        hash = generate_password_hash(request.form.get("password"))

        # Save username and hashed password to database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Render registration template
        return render_template("registration.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure stock symbol was submitted
        if not request.form.get("symbol"):
            return apology("must provide stock symbol", 400)

        # Ensure number of shares was submitted
        elif not request.form.get("shares"):
            return apology("must provide number of shares", 400)

        # Look up the stock symbol
        stock = lookup(request.form.get("symbol"))

        # Query database for current user id with stock symbol
        rows = db.execute("SELECT * FROM portfolio WHERE user_id = ? AND stock_symbol = ?", session["user_id"], stock["symbol"])

        # Get current number of shares of the stock user have
        current_shares_amount = rows[0]["stock_amount"]

        # Validate number of shares
        # Handles non-numeric shares
        if not (request.form.get("shares")).isdigit():
            return apology("invalid number of shares", 400)

        # Check valid amount of shares can sell
        shares = int(request.form.get("shares"))
        if shares > current_shares_amount:
            return apology("invalid number of shares", 400)

        # Query database for current user id from users table
        row = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # Get the amount of cash user have from the row
        cash = row[0]["cash"]

        # Calculate the amount of transaction
        sold = stock["price"] * shares

        # Calculate the balance after sold the stocks
        balance = cash + sold

        # Update cash balance of user after transaction
        db.execute("UPDATE users SET cash = ? WHERE id = ?", balance, session["user_id"])

        # Update transaction to the history table
        db.execute("INSERT INTO history (user_id, stock_symbol, stock_amount, stock_price, total_value, method) VALUES (?, ?, ?, ?, ?, ?)",
                   session["user_id"], stock["symbol"], shares, stock["price"], sold, "Sell")

        # Update shares in portfolio table
        # Check whether the user sold all that stock in portfolio
        # If the user don't have any left in portfolio, delete that stock from the portfolio table
        if shares == current_shares_amount:
            db.execute("DELETE FROM portfolio WHERE user_id = ? AND stock_symbol = ?", session["user_id"], stock["symbol"])

        # If the user still have some of that stocks left, update the amount of shares to the portfolio table
        else:

            # Calculate new amount of shares after the transaction
            remain_shares_amount = current_shares_amount - shares

            # Update new amount of shares in portfolio table
            db.execute("UPDATE portfolio SET stock_amount = ? WHERE user_id = ? AND stock_symbol = ?",
                       remain_shares_amount, session["user_id"], stock["symbol"])

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Query database for current user id from portfolio table
        df = db.execute("SELECT * FROM portfolio WHERE user_id = ?", session["user_id"])

        # Render sell template
        return render_template("sell.html", df=df)


@app.route("/changePassword", methods=["GET", "POST"])
def changePassword():
    """Change user password"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure current password was submitted
        if not request.form.get("currentpassword"):
            return apology("must provide your current password", 400)

        # Ensure new password was submitted
        elif not request.form.get("newpassword"):
            return apology("must provide your new password", 400)

        # Ensure the password is match
        elif request.form.get("newpassword") != request.form.get("confirmation"):
            return apology("password not match", 400)

        # Query database for current user id from users table
        row = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # Ensure current password correct
        if not check_password_hash(row[0]["hash"], request.form.get("currentpassword")):
            return apology("invalid current password", 400)

        # Get the new password hashed by encryption function
        hash = generate_password_hash(request.form.get("newpassword"))

        # Update new hashed password to database
        db.execute("UPDATE users SET hash = ? WHERE id = ?", hash, session["user_id"])

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Render changePassword template
        return render_template("changePassword.html")

@app.route("/addcash", methods=["GET", "POST"])
def addCash():
    """Allow user to add cash to their funds"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure cash amount was submitted
        if not request.form.get("addcash"):
            return apology("must provide your added cash amount", 400)

        # Validate added cash amount
        # Handles non-numeric cash amount
        if not (request.form.get("addcash")).isdigit():
            return apology("invalid cash amount", 400)

        # Query database for current user id from users table
        row = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # Get current fund
        fund = row[0]["cash"]

        # Get the added cash amount
        added_cash = int(request.form.get("addcash"))

        # Calculate new fund amount for the user
        new_fund = fund + added_cash

        # Update new fund amount for the user to database
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_fund, session["user_id"])

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Render addcash template
        return render_template("addcash.html")