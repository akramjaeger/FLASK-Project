# Flask Marketplace (Gift Cards + Video Games)

A simple marketplace built with Flask, HTML, CSS, and MySQL (XAMPP).

## Features
- List gift cards and video games
- Filter by category and search by title/platform/region
- View product details
- Login system with roles (`admin`, `user`)
- Only admin can add new products
- Admin can list, edit, hide/unhide, and delete products
- User cart flow: add items, update quantity, remove items, and checkout

## 1) XAMPP Database Setup
1. Start **Apache** and **MySQL** from XAMPP Control Panel.
2. Open phpMyAdmin: `http://localhost/phpmyadmin`.
3. Create or update the database by running the SQL in `database/schema.sql`.
4. If you already had an older version of this project, run these migrations in order:
   - `database/migration_auth.sql`
   - `database/migration_admin_cart.sql`
4. Default seeded accounts:
   - Admin: `admin` / `admin123`
   - User: `player1` / `user123`

## 2) Python Setup
1. Open terminal in this project folder.
2. Create venv:
   - Windows: `python -m venv .venv`
3. Activate venv:
   - Windows PowerShell: `.\\.venv\\Scripts\\Activate.ps1`
4. Install dependencies:
   - `pip install -r requirements.txt`

## 3) Environment Variables
1. Copy `.env.example` to `.env`.
2. Update values if needed (especially `MYSQL_PASSWORD` if your MySQL root has a password).

## 4) Run App
- `flask --app app run --debug`
- Open `http://127.0.0.1:5000`

## Routes
- `/` home page
- `/products` all listings
- `/product/<id>` listing details
- `/login` user/admin login
- `/logout` logout
- `/admin/products/new` add new listing (admin only)
- `/admin/products` admin product manager (grid/list actions)
- `/admin/products/<id>/edit` admin edit product
- `/admin/products/<id>/toggle-visibility` admin hide/unhide product
- `/admin/products/<id>/delete` admin delete product
- `/cart` user cart page
- `/cart/add/<id>` add product to cart
- `/cart/update/<id>` update cart quantity
- `/cart/remove/<id>` remove cart item
- `/checkout` place order and decrease stock
