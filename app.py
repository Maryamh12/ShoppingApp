"""
Shopping App — Flask Backend
Polished and secured from the original project.

Security improvements:
- Parameterised queries throughout (prevents SQL injection)
- Stripe PaymentIntent API (replaces deprecated Charge API)
- Password validation (min 8 chars) on register
- Login required decorator for protected routes
- Per-user authorisation on basket, wishlist and orders (403 on mismatch)
- CSRF tokens on every state-changing POST
- Idempotent order recording keyed on the Stripe PaymentIntent id
- Session basket_count for navbar badge
- No sensitive keys in source (use environment variables)
"""

import os
import sqlite3
import secrets
import stripe
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort
)
from flask_cors import CORS

# ── App setup ─────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# Use environment variables in production; fall back to placeholders for dev
app.config['SECRET_KEY']          = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
stripe.api_key                    = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_YOUR_KEY_HERE')
STRIPE_PUBLIC_KEY                 = os.environ.get('STRIPE_PUBLIC_KEY',  'pk_test_YOUR_KEY_HERE')
DB_PATH                           = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'productdb.db'))

# Harden the session cookie
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE']   = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
#

# ── Database helper ───────────────────────────────────────────

def get_db():
    """Open a database connection with row_factory for dict-like access."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


# ── CSRF helpers ──────────────────────────────────────────────

def generate_csrf():
    """Generate and store a CSRF token in the session."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


def validate_csrf():
    """Validate the CSRF token submitted with a POST request."""
    token = session.get('csrf_token')
    submitted = request.form.get('csrf_token')
    if not token or not submitted or not secrets.compare_digest(token, submitted):
        abort(403)


# Expose csrf_token to all templates automatically
@app.context_processor
def inject_csrf():
    return dict(csrf_token=generate_csrf(), stripe_public_key=STRIPE_PUBLIC_KEY)


# ── Login-required decorator ──────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('logged_out', True):
            flash('Please log in to access that page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ── Session initialisation ────────────────────────────────────

@app.before_request
def init_session():
    session.setdefault('logged_out', True)
    session.setdefault('user_id', 0)
    session.setdefault('basket_count', 0)
    session.setdefault('username', '')
    session.setdefault('email', '')


def refresh_basket_count():
    """Update the basket item count stored in session (used by navbar badge)."""
    user_id = session.get('user_id', 0)
    if not user_id:
        session['basket_count'] = 0
        return
    with get_db() as con:
        cur = con.cursor()
        cur.execute('SELECT COALESCE(SUM(quantity), 0) FROM Basket WHERE user_id = ?', (user_id,))
        session['basket_count'] = cur.fetchone()[0]


# ── Data helpers ──────────────────────────────────────────────

def get_products():
    with get_db() as con:
        return con.execute('SELECT * FROM products').fetchall()


def get_product_by_id(product_id):
    with get_db() as con:
        product  = con.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        comments = con.execute('SELECT * FROM review WHERE product_id = ?', (product_id,)).fetchall()
    return product, comments


def get_basket_items(user_id):
    with get_db() as con:
        return con.execute("""
            SELECT p.name, p.description, b.quantity, p.price, p.image_url, p.id
            FROM Basket b
            JOIN products p ON b.product_id = p.id
            WHERE b.user_id = ?
        """, (user_id,)).fetchall()


def basket_total(items):
    return sum(item[2] * item[3] for item in items)


# ── Public routes ─────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('home.html', title='Home')


@app.route('/products')
def products():
    return render_template('products.html', title='Products', members=get_products())


@app.route('/product/<int:member_id>')
def product(member_id):
    item, comments = get_product_by_id(member_id)
    if item is None:
        flash('Product not found.', 'error')
        return redirect(url_for('products'))
    return render_template('product.html', title=item['name'], member=item, comments=comments)


# ── Auth routes ───────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not session.get('logged_out', True):
        return redirect(url_for('products'))

    if request.method == 'POST':
        validate_csrf()

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('login'))

        try:
            with get_db() as con:
                row = con.execute(
                    'SELECT user_id, password, email FROM users WHERE username = ?', (username,)
                ).fetchone()

            if row and check_password_hash(row['password'], password):
                # Start a fresh session on login (prevents session fixation);
                # a new CSRF token is generated on the next page render
                session.clear()
                session['logged_out']  = False
                session['user_id']     = row['user_id']
                session['username']    = username
                session['email']       = row['email']
                refresh_basket_count()
                flash(f'Welcome back, {username}!', 'success')
                return redirect(url_for('products'))

            flash('Invalid username or password.', 'error')
        except Exception as e:
            app.logger.error('Login error: %s', e)
            flash('An unexpected error occurred. Please try again.', 'error')

    return render_template('login.html', title='Sign In')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if not session.get('logged_out', True):
        return redirect(url_for('products'))

    if request.method == 'POST':
        validate_csrf()

        username         = request.form.get('username', '').strip()
        email            = request.form.get('email', '').strip().lower()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        for err in errors:
            flash(err, 'error')
        if errors:
            return redirect(url_for('register'))

        hashed = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

        try:
            with get_db() as con:
                con.execute(
                    'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                    (username, hashed, email)
                )
                con.commit()
            flash('Account created! Please sign in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('That username or email is already taken.', 'error')
        except Exception as e:
            app.logger.error('Register error: %s', e)
            flash('An unexpected error occurred.', 'error')

    return render_template('register.html', title='Create Account')


@app.route('/logout')
def logout():
    username = session.get('username', 'User')
    session.clear()
    session['logged_out'] = True
    session['user_id']    = 0
    flash(f'Goodbye, {username}! You have been logged out.', 'success')
    return redirect(url_for('home'))


# ── Basket routes ─────────────────────────────────────────────

@app.route('/basket/<int:user_id>')
def basket(user_id):
    if session.get('logged_out', True):
        return render_template('basket.html', title='Basket', basketItems=[], username=None)

    # Users may only view their own basket
    if user_id != session.get('user_id'):
        abort(403)

    username     = session.get('username')
    basket_items = get_basket_items(user_id)
    return render_template('basket.html', title='Basket', basketItems=basket_items, username=username)


@app.route('/products/<int:user_id>/<int:product_id>', methods=['POST'])
@login_required
def addtobasket(user_id, product_id):
    validate_csrf()

    if user_id != session.get('user_id'):
        abort(403)

    quantity = max(1, request.form.get('quantity', 1, type=int))

    try:
        with get_db() as con:
            existing = con.execute(
                'SELECT quantity FROM Basket WHERE user_id = ? AND product_id = ?',
                (user_id, product_id)
            ).fetchone()

            if existing:
                con.execute(
                    'UPDATE Basket SET quantity = ? WHERE user_id = ? AND product_id = ?',
                    (existing['quantity'] + quantity, user_id, product_id)
                )
            else:
                con.execute(
                    'INSERT INTO Basket (user_id, product_id, quantity) VALUES (?, ?, ?)',
                    (user_id, product_id, quantity)
                )
            con.commit()

        refresh_basket_count()
        flash('Item added to your basket!', 'success')
    except Exception as e:
        app.logger.error('Add to basket error: %s', e)
        flash('Could not add item. Please try again.', 'error')

    return redirect(url_for('product', member_id=product_id))


@app.route('/update-basket/<int:user_id>/<int:product_id>', methods=['POST'])
@login_required
def update_basket(user_id, product_id):
    validate_csrf()

    if user_id != session.get('user_id'):
        abort(403)

    action = request.form.get('action')

    try:
        with get_db() as con:
            if action == 'update':
                qty = request.form.get('quantity', type=int)
                if qty and qty > 0:
                    con.execute(
                        'UPDATE Basket SET quantity = ? WHERE user_id = ? AND product_id = ?',
                        (qty, user_id, product_id)
                    )
                    flash('Basket updated.', 'success')
                else:
                    flash('Quantity must be at least 1.', 'error')
            elif action == 'remove':
                con.execute(
                    'DELETE FROM Basket WHERE user_id = ? AND product_id = ?',
                    (user_id, product_id)
                )
                flash('Item removed from basket.', 'success')
            con.commit()

        refresh_basket_count()
    except Exception as e:
        app.logger.error('Update basket error: %s', e)
        flash('Could not update basket.', 'error')

    return redirect(url_for('basket', user_id=user_id))


# ── Favourites routes ─────────────────────────────────────────

@app.route('/favorite/<int:user_id>')
def favorite(user_id):
    if session.get('logged_out', True):
        return render_template('favorite.html', title='Wishlist', favoritesItems=[], username=None)

    # Users may only view their own wishlist
    if user_id != session.get('user_id'):
        abort(403)

    with get_db() as con:
        items = con.execute("""
            SELECT p.name, p.description, p.price, p.image_url, p.id
            FROM Favorites f
            JOIN products p ON f.product_id = p.id
            WHERE f.user_id = ?
        """, (user_id,)).fetchall()

    return render_template('favorite.html', title='Wishlist',
                           favoritesItems=items, username=session.get('username'))


@app.route('/favorite/<int:user_id>/<int:product_id>', methods=['POST'])
@login_required
def addtofavorites(user_id, product_id):
    validate_csrf()

    if user_id != session.get('user_id'):
        abort(403)

    try:
        with get_db() as con:
            existing = con.execute(
                'SELECT 1 FROM Favorites WHERE user_id = ? AND product_id = ?',
                (user_id, product_id)
            ).fetchone()

            if existing:
                con.execute(
                    'DELETE FROM Favorites WHERE user_id = ? AND product_id = ?',
                    (user_id, product_id)
                )
                flash('Removed from your wishlist.', 'success')
            else:
                con.execute(
                    'INSERT INTO Favorites (user_id, product_id) VALUES (?, ?)',
                    (user_id, product_id)
                )
                flash('Saved to your wishlist!', 'success')
            con.commit()
    except Exception as e:
        app.logger.error('Favourite toggle error: %s', e)
        flash('Could not update wishlist.', 'error')

    return redirect(url_for('product', member_id=product_id))


@app.route('/update-favorite/<int:user_id>/<int:product_id>', methods=['POST'])
@login_required
def update_favorite(user_id, product_id):
    validate_csrf()

    if user_id != session.get('user_id'):
        abort(403)

    action = request.form.get('action')

    try:
        with get_db() as con:
            if action == 'update':
                # Move from wishlist to basket
                existing = con.execute(
                    'SELECT quantity FROM Basket WHERE user_id = ? AND product_id = ?',
                    (user_id, product_id)
                ).fetchone()

                if existing:
                    con.execute(
                        'UPDATE Basket SET quantity = ? WHERE user_id = ? AND product_id = ?',
                        (existing['quantity'] + 1, user_id, product_id)
                    )
                else:
                    con.execute(
                        'INSERT INTO Basket (user_id, product_id, quantity) VALUES (?, ?, ?)',
                        (user_id, product_id, 1)
                    )

                con.execute(
                    'DELETE FROM Favorites WHERE user_id = ? AND product_id = ?',
                    (user_id, product_id)
                )
                flash('Item moved to basket!', 'success')

            elif action == 'remove':
                con.execute(
                    'DELETE FROM Favorites WHERE user_id = ? AND product_id = ?',
                    (user_id, product_id)
                )
                flash('Removed from wishlist.', 'success')

            con.commit()

        refresh_basket_count()
    except Exception as e:
        app.logger.error('Update favourite error: %s', e)
        flash('Could not update wishlist.', 'error')

    return redirect(url_for('favorite', user_id=user_id))


# ── Reviews ───────────────────────────────────────────────────

@app.route('/update_comments/<int:user_id>/<int:product_id>', methods=['POST'])
@login_required
def update_comments(user_id, product_id):
    validate_csrf()

    if user_id != session.get('user_id'):
        abort(403)

    if request.form.get('action') == 'update':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()

        if not name or not description:
            flash('Please fill in both title and comment.', 'error')
            return redirect(url_for('product', member_id=product_id))

        try:
            with get_db() as con:
                con.execute(
                    'INSERT INTO review (user_id, product_id, name, description) VALUES (?, ?, ?, ?)',
                    (user_id, product_id, name, description)
                )
                con.commit()
            flash('Review submitted. Thank you!', 'success')
        except Exception as e:
            app.logger.error('Review error: %s', e)
            flash('Could not submit review.', 'error')

    return redirect(url_for('product', member_id=product_id))


# ── Checkout ──────────────────────────────────────────────────

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    user_id      = session['user_id']
    basket_items = get_basket_items(user_id)

    if not basket_items:
        flash('Your basket is empty.', 'error')
        return redirect(url_for('basket', user_id=user_id))

    order_total = basket_total(basket_items)

    if request.method == 'POST':
        validate_csrf()

        email             = request.form.get('email', '').strip()
        first_name        = request.form.get('first_name', '').strip()
        last_name         = request.form.get('last_name', '').strip()
        address           = request.form.get('address', '').strip()
        city              = request.form.get('city', '').strip()
        postcode          = request.form.get('postcode', '').strip()
        payment_method_id = request.form.get('payment_method_id', '').strip()

        # Server-side validation
        if not all([email, first_name, last_name, address, city, postcode, payment_method_id]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('checkout'))

        try:
            # Create PaymentIntent and confirm immediately
            intent = stripe.PaymentIntent.create(
                amount            = int(order_total * 100),   # pence
                currency          = 'gbp',
                payment_method    = payment_method_id,
                confirm           = True,
                return_url        = url_for('checkout_return', _external=True),
                receipt_email     = email,
                description       = f'Order for {first_name} {last_name}',
                metadata          = {
                    'user_id':   user_id,
                    'username':  session.get('username', ''),
                    'email':     email,
                },
                shipping = {
                    'name':    f'{first_name} {last_name}',
                    'address': {
                        'line1':       address,
                        'city':        city,
                        'postal_code': postcode,
                        'country':     'GB',
                    },
                },
                automatic_payment_methods = {
                    'enabled':          True,
                    'allow_redirects':  'never',
                },
            )

            if intent.status == 'succeeded':
                return _complete_order(user_id, basket_items, order_total, email, intent.id)

            # Requires further action (3DS etc.)
            flash('Your payment requires additional verification. Please try again.', 'error')

        except stripe.error.CardError as e:
            flash(f'Payment declined: {e.user_message}', 'error')
        except stripe.error.StripeError as e:
            app.logger.error('Stripe error: %s', e)
            flash('Payment service unavailable. Please try again later.', 'error')
        except Exception as e:
            app.logger.error('Checkout error: %s', e)
            flash('An unexpected error occurred.', 'error')

        return redirect(url_for('checkout'))

    return render_template('checkout.html', title='Checkout',
                           basket_items=basket_items, order_total=order_total)


def _complete_order(user_id, basket_items, total, email, stripe_intent_id):
    """
    Record the completed order in the database and clear the basket.
    Returns a redirect to the confirmation page.
    """
    order_ref = secrets.token_hex(4).upper()

    try:
        with get_db() as con:
            # Idempotency: never record the same payment twice (e.g. page refresh)
            existing = con.execute(
                'SELECT order_ref FROM Orders WHERE stripe_intent_id = ?', (stripe_intent_id,)
            ).fetchone()
            if existing:
                return redirect(url_for('order_confirm', order_ref=existing['order_ref'],
                                        email=email, total=f'{total:.2f}'))

            # Insert order header
            cur = con.execute(
                """INSERT INTO Orders (user_id, order_date, total, status, stripe_intent_id, order_ref)
                   VALUES (?, datetime('now'), ?, 'paid', ?, ?)""",
                (user_id, total, stripe_intent_id, order_ref)
            )
            order_id = cur.lastrowid

            # Insert order lines
            for item in basket_items:
                con.execute(
                    """INSERT INTO OrderDetails
                       (order_id, product_id, quantity, price_at_time_of_order)
                       VALUES (?, ?, ?, ?)""",
                    (order_id, item['id'], item['quantity'], item['price'])
                )

            # Clear basket
            con.execute('DELETE FROM Basket WHERE user_id = ?', (user_id,))
            con.commit()

        session['basket_count'] = 0

        return redirect(url_for('order_confirm',
                                order_ref=order_ref,
                                email=email,
                                total=f'{total:.2f}'))

    except Exception as e:
        app.logger.error('Order recording error: %s', e)
        # Payment succeeded but DB failed — still redirect with success
        flash('Payment received! (Order details unavailable — please contact support.)', 'success')
        return redirect(url_for('products'))


@app.route('/checkout/return')
@login_required
def checkout_return():
    """Handle redirect returns from Stripe."""
    payment_intent_id = request.args.get('payment_intent')
    if payment_intent_id:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        user_id = session.get('user_id')

        # The payment must belong to the logged-in user
        if str(intent.metadata.get('user_id')) != str(user_id):
            abort(403)

        if intent.status == 'succeeded':
            basket_items = get_basket_items(user_id)
            total        = basket_total(basket_items)
            email        = intent.receipt_email or session.get('email', '')
            return _complete_order(user_id, basket_items, total, email, intent.id)
    flash('Payment could not be confirmed. Please contact support.', 'error')
    return redirect(url_for('products'))


@app.route('/order/confirm')
@login_required
def order_confirm():
    order_ref    = request.args.get('order_ref', 'N/A')
    email        = request.args.get('email', '')
    order_total  = float(request.args.get('total', 0))
    username     = session.get('username', '')

    # Fetch order items for summary
    with get_db() as con:
        order_items = con.execute("""
            SELECT p.name, p.description, od.quantity, od.price_at_time_of_order
            FROM Orders o
            JOIN OrderDetails od ON o.order_id = od.order_id
            JOIN products p ON od.product_id = p.id
            WHERE o.order_ref = ? AND o.user_id = ?
        """, (order_ref, session['user_id'])).fetchall()

    return render_template('order_confirm.html',
                           title='Order Confirmed',
                           order_ref=order_ref,
                           email=email,
                           order_total=order_total,
                           username=username,
                           order_items=order_items)


# ── Error handlers ────────────────────────────────────────────

@app.errorhandler(403)
def forbidden(e):
    flash('Access denied.', 'error')
    return redirect(url_for('home'))


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html', title='Page Not Found'), 404


# ── Entry point ───────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
