from decimal import Decimal, InvalidOperation
import os
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from werkzeug.security import check_password_hash

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret")

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DB", "marketplace_db"),
}


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def is_logged_in():
    return bool(session.get("user_id"))


def is_admin():
    return session.get("role") == "admin"


def is_user():
    return session.get("role") == "user"


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_logged_in():
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_logged_in():
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        if not is_admin():
            flash("Only admin can access this page.", "error")
            return redirect(url_for("products"))
        return view(*args, **kwargs)

    return wrapped


def user_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_logged_in():
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        if not is_user():
            flash("This action is available for user accounts only.", "error")
            return redirect(url_for("products"))
        return view(*args, **kwargs)

    return wrapped


def get_cart_count(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COALESCE(SUM(quantity), 0)
            FROM cart_items
            WHERE user_id = %s
            """,
            (user_id,),
        )
        result = cursor.fetchone()
        return int(result[0] or 0)
    except Error:
        return 0
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


@app.context_processor
def inject_user_state():
    user_id = session.get("user_id")
    cart_count = get_cart_count(user_id) if user_id and is_user() else 0
    return {
        "is_logged_in": is_logged_in(),
        "is_admin": is_admin(),
        "is_user": is_user(),
        "current_username": session.get("username"),
        "cart_count": cart_count,
    }


@app.route("/login", methods=["GET", "POST"])
def login():
    if is_logged_in():
        return redirect(url_for("products"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template("login.html")

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, username, password_hash, role
                FROM users
                WHERE username = %s
                LIMIT 1
                """,
                (username,),
            )
            user = cursor.fetchone()
        except Error:
            flash("Login failed due to database connection issue.", "error")
            return render_template("login.html")
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid username or password.", "error")
            return render_template("login.html")

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        flash(f"Welcome, {user['username']}.", "success")
        return redirect(url_for("products"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/")
def home():
    featured = []
    error_message = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, title, category, platform, region, price, stock, image_url, is_hidden
            FROM products
            WHERE is_hidden = 0
            ORDER BY created_at DESC
            LIMIT 6
            """
        )
        featured = cursor.fetchall()
    except Error:
        error_message = "Database connection failed. Check your XAMPP MySQL settings."
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

    return render_template("index.html", featured=featured, error_message=error_message)


@app.route("/products")
def products():
    selected_category = request.args.get("category", "")
    search_query = request.args.get("q", "").strip()

    filters = []
    values = []

    if not is_admin():
        filters.append("is_hidden = 0")

    if selected_category in {"gift_card", "video_game"}:
        filters.append("category = %s")
        values.append(selected_category)

    if search_query:
        filters.append("(title LIKE %s OR platform LIKE %s OR region LIKE %s)")
        like_value = f"%{search_query}%"
        values.extend([like_value, like_value, like_value])

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    items = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            f"""
            SELECT id, title, category, platform, region, price, stock, image_url, is_hidden
            FROM products
            {where_clause}
            ORDER BY created_at DESC
            """,
            tuple(values),
        )
        items = cursor.fetchall()
    except Error:
        flash("Could not fetch products from database.", "error")
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

    return render_template(
        "products.html",
        items=items,
        selected_category=selected_category,
        search_query=search_query,
    )


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    item = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, title, category, platform, region, price, stock, description, image_url, created_at, is_hidden
            FROM products
            WHERE id = %s
            """,
            (product_id,),
        )
        item = cursor.fetchone()
    except Error:
        flash("Could not load the selected product.", "error")
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

    if not item:
        flash("Product not found.", "error")
        return redirect(url_for("products"))

    if item["is_hidden"] and not is_admin():
        flash("Product not found.", "error")
        return redirect(url_for("products"))

    return render_template("product_detail.html", item=item)


@app.route("/admin/products")
@admin_required
def admin_products():
    items = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, title, category, platform, region, price, stock, image_url, is_hidden, created_at
            FROM products
            ORDER BY created_at DESC
            """
        )
        items = cursor.fetchall()
    except Error:
        flash("Could not load products.", "error")
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

    return render_template("admin_products.html", items=items)


@app.route("/admin/products/new", methods=["GET", "POST"])
@admin_required
def admin_add_product():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        platform = request.form.get("platform", "").strip()
        region = request.form.get("region", "").strip()
        price_raw = request.form.get("price", "").strip()
        stock_raw = request.form.get("stock", "").strip()
        image_url = request.form.get("image_url", "").strip()
        description = request.form.get("description", "").strip()

        errors = []

        if not title:
            errors.append("Title is required.")

        if category not in {"gift_card", "video_game"}:
            errors.append("Category must be gift_card or video_game.")

        try:
            price = Decimal(price_raw)
            if price <= 0:
                errors.append("Price must be greater than 0.")
        except InvalidOperation:
            errors.append("Price must be a valid number.")
            price = None

        try:
            stock = int(stock_raw)
            if stock < 0:
                errors.append("Stock cannot be negative.")
        except ValueError:
            errors.append("Stock must be a whole number.")
            stock = None

        if errors:
            for msg in errors:
                flash(msg, "error")
            return render_template("add_product.html")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO products (title, category, platform, region, price, stock, image_url, description, is_hidden)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0)
                """,
                (title, category, platform, region, price, stock, image_url, description),
            )
            conn.commit()
            flash("Product added successfully.", "success")
            return redirect(url_for("admin_products"))
        except Error:
            flash("Failed to add product. Please check database connection.", "error")
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    return render_template("add_product.html")


@app.route("/admin/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_product(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            category = request.form.get("category", "").strip()
            platform = request.form.get("platform", "").strip()
            region = request.form.get("region", "").strip()
            price_raw = request.form.get("price", "").strip()
            stock_raw = request.form.get("stock", "").strip()
            image_url = request.form.get("image_url", "").strip()
            description = request.form.get("description", "").strip()

            errors = []
            if not title:
                errors.append("Title is required.")
            if category not in {"gift_card", "video_game"}:
                errors.append("Category must be gift_card or video_game.")

            try:
                price = Decimal(price_raw)
                if price <= 0:
                    errors.append("Price must be greater than 0.")
            except InvalidOperation:
                errors.append("Price must be a valid number.")
                price = None

            try:
                stock = int(stock_raw)
                if stock < 0:
                    errors.append("Stock cannot be negative.")
            except ValueError:
                errors.append("Stock must be a whole number.")
                stock = None

            if errors:
                for msg in errors:
                    flash(msg, "error")
                cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
                item = cursor.fetchone()
                return render_template("edit_product.html", item=item)

            update_cursor = conn.cursor()
            update_cursor.execute(
                """
                UPDATE products
                SET title = %s,
                    category = %s,
                    platform = %s,
                    region = %s,
                    price = %s,
                    stock = %s,
                    image_url = %s,
                    description = %s
                WHERE id = %s
                """,
                (title, category, platform, region, price, stock, image_url, description, product_id),
            )
            conn.commit()
            update_cursor.close()
            flash("Product updated.", "success")
            return redirect(url_for("admin_products"))

        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        item = cursor.fetchone()
        if not item:
            flash("Product not found.", "error")
            return redirect(url_for("admin_products"))
        return render_template("edit_product.html", item=item)

    except Error:
        flash("Database error while editing product.", "error")
        return redirect(url_for("admin_products"))
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


@app.route("/admin/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def admin_delete_product(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        flash("Product deleted.", "success")
    except Error:
        flash("Could not delete product.", "error")
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

    return redirect(url_for("admin_products"))


@app.route("/admin/products/<int:product_id>/toggle-visibility", methods=["POST"])
@admin_required
def admin_toggle_product_visibility(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE products
            SET is_hidden = CASE WHEN is_hidden = 1 THEN 0 ELSE 1 END
            WHERE id = %s
            """,
            (product_id,),
        )
        conn.commit()
        flash("Product visibility updated.", "success")
    except Error:
        flash("Could not update product visibility.", "error")
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

    return redirect(url_for("admin_products"))


@app.route("/cart")
@user_required
def cart():
    rows = []
    subtotal = Decimal("0.00")

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT p.id AS product_id,
                   p.title,
                   p.price,
                   p.stock,
                   p.image_url,
                   p.is_hidden,
                   ci.quantity
            FROM cart_items ci
            JOIN products p ON p.id = ci.product_id
            WHERE ci.user_id = %s
            ORDER BY ci.updated_at DESC
            """,
            (session["user_id"],),
        )
        rows = cursor.fetchall()

        for row in rows:
            subtotal += Decimal(row["price"]) * row["quantity"]
    except Error:
        flash("Could not load cart.", "error")
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

    return render_template("cart.html", rows=rows, subtotal=subtotal)


@app.route("/cart/add/<int:product_id>", methods=["POST"])
@user_required
def cart_add(product_id):
    quantity_raw = request.form.get("quantity", "1")
    try:
        quantity = int(quantity_raw)
    except ValueError:
        quantity = 1

    if quantity < 1:
        quantity = 1

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, title, stock, is_hidden
            FROM products
            WHERE id = %s
            """,
            (product_id,),
        )
        product = cursor.fetchone()

        if not product or product["is_hidden"]:
            flash("Product is not available.", "error")
            return redirect(url_for("products"))

        if product["stock"] <= 0:
            flash("Item is out of stock.", "error")
            return redirect(url_for("products"))

        cursor.execute(
            """
            SELECT quantity
            FROM cart_items
            WHERE user_id = %s AND product_id = %s
            """,
            (session["user_id"], product_id),
        )
        current = cursor.fetchone()

        new_qty = quantity
        if current:
            new_qty = current["quantity"] + quantity

        if new_qty > product["stock"]:
            new_qty = product["stock"]

        upsert = conn.cursor()
        if current:
            upsert.execute(
                """
                UPDATE cart_items
                SET quantity = %s
                WHERE user_id = %s AND product_id = %s
                """,
                (new_qty, session["user_id"], product_id),
            )
        else:
            upsert.execute(
                """
                INSERT INTO cart_items (user_id, product_id, quantity)
                VALUES (%s, %s, %s)
                """,
                (session["user_id"], product_id, new_qty),
            )

        conn.commit()
        upsert.close()
        flash(f"Added {product['title']} to cart.", "success")
    except Error:
        flash("Could not add item to cart.", "error")
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

    return redirect(request.referrer or url_for("products"))


@app.route("/cart/update/<int:product_id>", methods=["POST"])
@user_required
def cart_update(product_id):
    quantity_raw = request.form.get("quantity", "1")
    try:
        quantity = int(quantity_raw)
    except ValueError:
        quantity = 1

    if quantity <= 0:
        return redirect(url_for("cart_remove", product_id=product_id))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT stock, is_hidden FROM products WHERE id = %s",
            (product_id,),
        )
        product = cursor.fetchone()

        if not product or product["is_hidden"]:
            flash("Product is no longer available.", "error")
            return redirect(url_for("cart_remove", product_id=product_id))

        if quantity > product["stock"]:
            quantity = product["stock"]

        update_cursor = conn.cursor()
        update_cursor.execute(
            """
            UPDATE cart_items
            SET quantity = %s
            WHERE user_id = %s AND product_id = %s
            """,
            (quantity, session["user_id"], product_id),
        )
        conn.commit()
        update_cursor.close()
        flash("Cart updated.", "success")
    except Error:
        flash("Could not update cart.", "error")
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:product_id>", methods=["POST"])
@user_required
def cart_remove(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM cart_items WHERE user_id = %s AND product_id = %s",
            (session["user_id"], product_id),
        )
        conn.commit()
        flash("Item removed from cart.", "success")
    except Error:
        flash("Could not remove item.", "error")
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

    return redirect(url_for("cart"))


@app.route("/checkout", methods=["POST"])
@user_required
def checkout():
    order_id = None

    try:
        conn = get_db_connection()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT p.id AS product_id,
                   p.title,
                   p.price,
                   p.stock,
                   p.is_hidden,
                   ci.quantity
            FROM cart_items ci
            JOIN products p ON p.id = ci.product_id
            WHERE ci.user_id = %s
            FOR UPDATE
            """,
            (session["user_id"],),
        )
        items = cursor.fetchall()

        if not items:
            conn.rollback()
            flash("Your cart is empty.", "error")
            return redirect(url_for("cart"))

        total = Decimal("0.00")
        for item in items:
            if item["is_hidden"]:
                conn.rollback()
                flash(f"{item['title']} is no longer available.", "error")
                return redirect(url_for("cart"))
            if item["quantity"] > item["stock"]:
                conn.rollback()
                flash(f"Not enough stock for {item['title']}.", "error")
                return redirect(url_for("cart"))
            total += Decimal(item["price"]) * item["quantity"]

        order_cursor = conn.cursor()
        order_cursor.execute(
            """
            INSERT INTO orders (user_id, total_amount, status)
            VALUES (%s, %s, 'paid')
            """,
            (session["user_id"], total),
        )
        order_id = order_cursor.lastrowid

        for item in items:
            order_cursor.execute(
                """
                INSERT INTO order_items (order_id, product_id, title_snapshot, price_snapshot, quantity)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    order_id,
                    item["product_id"],
                    item["title"],
                    item["price"],
                    item["quantity"],
                ),
            )
            order_cursor.execute(
                "UPDATE products SET stock = stock - %s WHERE id = %s",
                (item["quantity"], item["product_id"]),
            )

        order_cursor.execute(
            "DELETE FROM cart_items WHERE user_id = %s",
            (session["user_id"],),
        )

        conn.commit()
        order_cursor.close()
        flash(f"Purchase successful. Order #{order_id} created.", "success")
        return redirect(url_for("products"))

    except Error:
        try:
            conn.rollback()
        except Exception:
            pass
        flash("Checkout failed. Please try again.", "error")
        return redirect(url_for("cart"))
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    app.run(debug=True)
