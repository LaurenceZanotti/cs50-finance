import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
# app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
# db = SQL("sqlite:///finance.db")

# Configure CS50 Library to use Postgres database
uri = os.getenv("DATABASE_URL")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://")
db = SQL(uri)

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    stocks = db.execute("SELECT symbol, company, shares, price, total FROM user_stocks WHERE user_id = :user_id AND isOwned = :isOwned GROUP BY user_stocks.stock_id, user_stocks.symbol", user_id = session["user_id"], isOwned = 1)
    cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = session["user_id"])

    # Format stocks
    for stock in stocks:
        # Check current stock price
        quote = lookup(stock["symbol"])
        stock["currentPrice"] = usd(quote["price"])

        # Format fields
        stock["price"] = usd(stock["price"])
        stock["total"] = usd(stock["total"])

        # Get current total price of shares
        stock["currentTotal"] = usd(int(stock["shares"]) * quote["price"])


    return render_template("index.html", stocks = stocks, cash = usd(cash[0]["cash"]))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Ensures shares is a number
        if not shares.isnumeric():
            return apology("Must provide a positive number", 403)

        shares = int(shares)

        # When input is blank
        if not symbol:
            return apology("Must provide a symbol", 403)
        if not shares:
            return apology("Must provide number of shares to buy", 403)

        # Ensures symbol is valid
        if len(symbol) > 4 or len(symbol) < 1:
            return apology("Symbol should have 1 to 4 letters", 403)

        # Ensure symbol is valid
        if not symbol.isalpha():
            return apology("Symbol must be a letter", 403)

        # If no shares/company were found
        quote = lookup(symbol)
        if not quote:
            return apology("Company not found", 404)

        # Return user's cash
        cash = db.execute("SELECT cash FROM users WHERE id = :ident", ident = session["user_id"])

        # Simulate buy
        total = shares * quote['price']
        balance = cash[0]["cash"] - total

        # Unable to buy if the balance is due
        if balance < 0:
            return apology("Not enough resources for this operation", 403)

        # Insert stocks, or update current stock if it already exists ((BEGINNING OF A TRANSACTION))
        symbols = db.execute("SELECT stock_id, symbol, price, shares, total FROM user_stocks WHERE user_id = :user_id AND isOwned = :isOwned",
            user_id = session["user_id"],
            isOwned = 1
        )

        stock_id = None

        # Insert new stock when there's no stocks
        if not symbols:
            stock_id = db.execute("INSERT INTO user_stocks (user_id, symbol, company, shares, price, total, isOwned) VALUES (:user_id, :symbol, :company, :shares, :price, :total, :isOwned)",
                user_id = session["user_id"],
                symbol = quote["symbol"],
                company = quote["name"],
                shares = shares,
                price = quote["price"],
                total = total,
                isOwned = 1
            )


        # Or update current stock row
        else:
            # For each row in symbols, check if inputted symbol matches
            match = False
            for row in symbols:
                # If matches, update the current stock data summing its values
                if row["symbol"] in symbol:
                    updatePrint = db.execute("UPDATE user_stocks SET shares = :shares, total = :total, isOwned = :isOwned WHERE symbol = :symbol AND stock_id = :stock_id",
                        shares = shares + row["shares"],
                        total = total + row["total"],
                        isOwned = 1,
                        symbol = row["symbol"],
                        stock_id = row["stock_id"],
                    )

                    match = True
                    stock_id = row["stock_id"]

                    break

            # If there's no matches, insert new company symbol and its stocks
            if not match:
                    stock_id = db.execute("INSERT INTO user_stocks (user_id, symbol, company, shares, price, total, isOwned) VALUES (:user_id, :symbol, :company, :shares, :price, :total, :isOwned)",
                    user_id = session["user_id"],
                    symbol = quote["symbol"],
                    company = quote["name"],
                    shares = shares,
                    price = quote["price"],
                    total = total,
                    isOwned = 1
                )


        # Current date and time object
        now = datetime.now()

        # Add transaction history
        transactionId = db.execute("INSERT INTO transactions (user_id, stock_id, shares, sale_price, transact, date) VALUES (:user_id, :stock_id, :shares, :sale_price, :transact, :date)",
            user_id = session["user_id"],
            stock_id = stock_id,
            shares = shares,
            sale_price = quote["price"],
            transact = "b",
            date = now.strftime("%Y/%m/%d %H:%M:%S")
        )

        # Update user's cash
        db.execute("UPDATE users SET cash = :cash WHERE id = :user_id", cash = balance, user_id = session["user_id"])

        # Give the user feedback
        flash(f"Bought new stocks from { quote['name'] }!", "info")

        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Get user's history
    history = db.execute("SELECT symbol, transactions.shares, sale_price, date, transact FROM user_stocks JOIN transactions ON transactions.stock_id = user_stocks.stock_id WHERE user_stocks.user_id = :user_id ORDER BY transactions.id DESC",
        user_id = session["user_id"]
    )

    # Format data
    for item in history:
        item["sale_price"] = usd(item["sale_price"])

    return render_template("history.html", history = history)




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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        # Gives the user feedback
        flash("You were logged in successfully!", "success")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
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
    if request.method == "POST":

        symbol = request.form.get("symbol")

        # If field is blank
        if not symbol:
            return apology("Must provide a symbol", 403)

        # Ensures symbol is valid
        if len(symbol) > 4 or len(symbol) < 1:
            return apology("Symbol should have 1 to 4 letters", 403)

        # Ensure symbol is valid
        if not symbol.isalpha():
            return apology("Symbol must be a letter", 403)

        # Fetch quotes
        quotes = lookup(request.form.get("symbol"))

        # If the company doesn't exist
        if not quotes:
            return apology("Company doesn't exist", 404)

        # Format price to USD
        quotes["price"] = usd(quotes["price"])

        return render_template("quoted.html", quotes = quotes)
    else:
        return render_template("quote.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Delivers page if GET or create account if POST
    if request.method == "POST":
        name = request.form.get("username")
        pw = request.form.get("password")
        cpw = request.form.get("confirmation")

        # Check if all forms were filled
        if not name:
            return apology("must provide an username", 403)
        if not pw:
            return apology("must provide a password", 403)
        if not cpw:
            return apology("must confirm your password", 403)

        # Ensure username has at least 3 characters
        if len(name) < 3:
            flash(f"Username must have at least 3 characters", "warning")
            return redirect("/register")

        # Check if provided passwords match
        if pw != cpw:
            return apology("the provided passwords don't match", 403)

        # Returns apology if username exists
        rows = db.execute("SELECT * FROM users WHERE username = :username", username = name)
        if len(rows) == 1:
            return apology("username already in use", 403)

        # Register the user to the database
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :password)",
            username = name,
            password = generate_password_hash(pw))

        # Give user feedback
        flash("Your account was created!", "info")

        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    symbols = db.execute("SELECT DISTINCT stock_id, symbol FROM user_stocks WHERE user_id = :user_id AND isOwned = 1", user_id = session["user_id"])

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Ensure shares is a number
        if not shares.isnumeric():
            return apology("Shares must be a positive number", 403)

        # Ensure proper form submit
        if not symbol or symbol == "null":
            return apology("Must provide a symbol", 403)
        if not shares:
            return apology("Must provide a number of shares", 403)

        # Ensures symbol is valid
        if len(symbol) > 4 or len(symbol) < 1:
            return apology("Symbol should have 1 to 4 letters", 403)

        # Ensure symbol is valid
        if not symbol.isalpha():
            return apology("Symbol must be a letter", 403)

        # Check if symbol is within symbols
        symbolId = None
        invalid = False
        for item in symbols:
            if symbol in item["symbol"]:
                invalid = False
                symbolId = item["stock_id"]
                break
            else:
                invalid = True
        if invalid:
            return apology("Invalid symbol", 403)

        shares = int(shares)

        if shares < 1:
            return apology("Shares must be a positive number", 403)

        # Ensures that the user owns the number of shares
        totalshares = db.execute("SELECT stock_id, shares, price, total FROM user_stocks WHERE user_id = :user_id AND symbol = :symbol AND isOwned = :isOwned",
            user_id = session["user_id"],
            symbol = symbol,
            isOwned = 1
        )

        # If no shares are owned from that symbol
        if not totalshares[0]["shares"]:
            return apology("You don't own any shares from that company", 403)

        # Converts shares into an integer
        maxshares = int(totalshares[0]["shares"])

        if maxshares < shares:
            return apology("You don't own that many shares", 403)

        share_difference = maxshares - shares

        # Simulate sell
        cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = session["user_id"])
        cash = cash[0]["cash"]

        quote = lookup(symbol)
        profit = shares * quote["price"]
        balance = cash + profit

        now = datetime.now()

        # Insert transaction
        db.execute("INSERT INTO transactions (user_id, stock_id, shares, sale_price, transact, date) VALUES (:user_id, :stock_id, :shares, :sale_price, :transact, :date)",
            user_id = session["user_id"],
            stock_id = symbolId,
            shares = shares,
            sale_price = quote["price"],
            transact = 's',
            date = now.strftime("%Y/%m/%d %H:%M:%S")
        )

        # Update user's cash
        db.execute("UPDATE users SET cash = :cash WHERE id = :user_id",
            cash = balance,
            user_id = session["user_id"]
        )

        # Update number of shares and total
        db.execute("UPDATE user_stocks SET shares = :new_shares, total = :new_total, isOwned = :isOwned WHERE stock_id = :stock_id AND user_id = :user_id",
            new_shares = share_difference,
            new_total = totalshares[0]["price"] * share_difference,
            isOwned = 0 if share_difference == 0 else 1,
            stock_id = totalshares[0]["stock_id"],
            user_id = session["user_id"]
        )

        # Give feedback to user
        flash(f"You have sold { shares } shares of { quote['name'] }!", "success")

        return redirect("/")
    else:
        return render_template("sell.html", symbols = symbols)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """ View and edit profile information """

    if request.method == "POST":

        # Change password form
        if "change-pw-form" in request.form:
            # Check if form is invalid
            if not request.form.get("oldPassword") or not request.form.get("newPassword") or not request.form.get("confirmation"):
                flash(f"You must fill all fields", "danger")
                return redirect("/profile")

            # Check if new password is confirmed
            if request.form.get("newPassword") != request.form.get("confirmation"):
                flash(f"Passwords don't match", "warning")
                return redirect("/profile")

            rows = db.execute("SELECT username, hash FROM users WHERE id = :user_id",
                user_id = session["user_id"]
            )

            # Check if old password match
            if not check_password_hash(rows[0]["hash"], request.form.get("oldPassword")):
                flash(f"Wrong password", "danger")
                return redirect("/profile")

            # Change password
            db.execute("UPDATE users SET hash = :hash_pw WHERE id = :user_id",
                hash_pw = generate_password_hash(request.form.get("newPassword")),
                user_id = session["user_id"]
            )

            # Give user feedback
            flash(f"You've changed your password successfully!", "success")

        return redirect("/profile")
    else:
        transactions = db.execute("SELECT COUNT(id) AS count FROM transactions WHERE user_id = :user_id",
            user_id = session["user_id"]
        )
        return render_template("profile.html", transactions = transactions[0]["count"])


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
