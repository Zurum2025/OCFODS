from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Food, Order, FoodCategory
import os


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

app.secret_key = "dev-secret-key"  # temporary

# =========================
# CONFIG
# =========================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads/vendor_logos")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ocfods.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================
# HELPERS
# =========================

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# =========================
# ROUTES
# =========================

# Landing Page
@app.route("/")
def landing_page():
    return render_template("index.html")

# Student Registration
@app.route("/register/student", methods=["GET", "POST"])
def stud_reg():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        password_hash = generate_password_hash(password)

        student = User(
            role="student",
            name= name,
            email=email,
            password=password_hash
        )

        db.session.add(student)
        db.session.commit()

        return redirect(url_for("studash"))

    return render_template("stud_reg.html")

# Vendor Registration
@app.route("/register/vendor", methods=["GET", "POST"])
def vendor_reg():
    if request.method == "POST":
        business_name = request.form.get("business_name")
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please log in.", "danger")
            return redirect(url_for("login"))

        password_hash = generate_password_hash(password)

        logo = request.files.get("logo")
        logo_filename = None

        if logo and allowed_file(logo.filename):
            filename = secure_filename(logo.filename)
            logo_filename = f"{email}_{filename}"
            logo.save(os.path.join(app.config["UPLOAD_FOLDER"], logo_filename))

        vendor = User(
            role="vendor",
            business_name=business_name,
            email=email,
            password=password_hash,
            logo=logo_filename
        )

        

        db.session.add(vendor)
        db.session.commit()
        
        login_user(vendor) 
        
        return redirect(url_for("food_setup"))

    return render_template("vendor_reg.html")

# Vendor food setup
@app.route("/vendor/food_setup", methods=["GET", "POST"])
@login_required
def food_setup():
    if current_user.role != "vendor":
        abort(403)

    if request.method == "POST":

        food_groups = {
            "Main Dish": request.form.getlist("main_dish[]"),
            "Sauce": request.form.getlist("sauce[]"),
            "Topping": request.form.getlist("topping[]"),
            "Drink": request.form.getlist("drink[]")
        }

        custom_foods = {
            "Main Dish": request.form.get("custom_main_dish"),
            "Sauce": request.form.get("custom_sauce"),
            "Topping": request.form.get("custom_topping"),
            "Drink": request.form.get("custom_drink")
        }

        for category_name, foods in food_groups.items():

            # QUERY first
            category_obj = FoodCategory.query.filter_by(
                name=category_name
            ).first()

            # Create if not exists
            if not category_obj:
                category_obj = FoodCategory(name=category_name)
                db.session.add(category_obj)
                db.session.flush()  # assigns ID

            for food_name in foods:
                db.session.add(Food(
                    name=food_name,
                    price=0.0,
                    vendor_id=current_user.id,
                    category_id=category_obj.id
                ))

        for category_name, food_name in custom_foods.items():
            if food_name:

                category_obj = FoodCategory.query.filter_by(
                    name=category_name
                ).first()

                if not category_obj:
                    category_obj = FoodCategory(name=category_name)
                    db.session.add(category_obj)
                    db.session.flush()

                db.session.add(Food(
                    name=food_name,
                    price=0.0,
                    vendor_id=current_user.id,
                    category_id=category_obj.id
                ))

        db.session.commit()
        flash("Menu saved successfully", "success")
        return redirect(url_for("vendor_menu"))

    return render_template("food_setup.html")



# Vendor dashboard
@app.route("/vendor/dashboard")
@login_required
def vendor_dashboard():
    if current_user.role != "vendor":
        abort(403)
    return render_template(
        "vendor/vendor_dashboard.html",
        vendor=current_user
        )

# Login applies to all users
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Invalid email or password", "danger")
            return redirect(url_for("login"))
        
        if not check_password_hash(user.password, password):
            flash("Invalid email or password", "danger")
            return redirect(url_for("login"))

        if not user.is_active:
            flash("Account disabled", "danger")
            return redirect(url_for("login"))
        
        login_user(user)

        if user.role == "admin":
            return redirect(url_for("admin_dashboard"))

        elif user.role == "vendor":
            return redirect(url_for("vendor_dashboard"))

        elif user.role == "student":
            return redirect(url_for("studash"))

        else:
            flash("Unauthorized role", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

# Student dashboard
@app.route("/student/dashboard")
def studash():
    return render_template("student/studash.html")

@app.route("/student/stu_food")
def stu_food():
    foods = Food.query.filter_by(availability=True).all()

    grouped_foods = {}
    for food in foods:
        category = food.category.name
        grouped_foods.setdefault(category, []).append(food)

    return render_template(
        "student/stu_food.html",
        grouped_foods=grouped_foods,
        foods=foods,
        student = current_user)
# Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("landing_page"))

# Vendor menu
@app.route("/vendor/vendor_menu")
def vendor_menu():
    user = require_vendor()
    foods = Food.query.filter_by(vendor_id=user.id).all()
    
    grouped_foods = {}
    for food in foods:
        category = food.category.name
        grouped_foods.setdefault(category, []).append(food)
    
    return render_template(
            "vendor/vendor_menu.html",
            grouped_foods = grouped_foods,
            vendor=user,
            foods=foods
        )

@app.route("/vendor/vendor_orders")
def vendor_orders():
    user = require_vendor()
    return render_template("vendor/vendor_orders.html", vendor=user)

@app.route("/vendor/settings", methods=["GET", "POST"])
@login_required
def vendor_settings():
    user = require_vendor()

    foods = Food.query.filter_by(vendor_id = current_user.id).all()

    if request.method == "POST":
        for food in foods:
            price = request.form.get(f"price_{food.id}")
            availability = request.form.get(f"available_{food.id}")

            if price is not None:
                food.price = float(price)

            food.availability = True if availability == "on" else False

        db.session.commit()
        flash("Menu updated successfully", "success")
        return redirect(url_for("vendor_settings"))

    return render_template("vendor/vendor_settings.html", 
                           vendor=current_user,
                           foods = foods
                           )

# =========================
# ADMIN ROUTES
# =========================

@app.route("/admin/admin_dashboard")
def admin_dashboard():
    admin = require_admin()

    return render_template(
        "admin/admin_dashboard.html",
        admin=admin,
        user_count=User.query.count(),
        food_count=Food.query.count(),
        order_count=Order.query.count()
    )

@app.route("/admin/admin_users")
def admin_users():
    admin = require_admin()
    users = User.query.all()

    return render_template(
        "admin/admin_users.html",
        admin=admin,
        users=users
    )

@app.route("/admin/admin_vendors")
def admin_vendors():
    admin = require_admin()
    vendors = User.query.filter_by(role="vendor").all()

    return render_template(
        "admin/admin_vendors.html",
        admin=admin,
        vendors=vendors
    )

@app.route("/admin/admin_foods")
def admin_foods():
    admin = require_admin()
    foods = Food.query.all()

    return render_template(
        "admin/admin_foods.html",
        admin=admin,
        foods=foods
    )
def seed_categories():
    categories = ["Main Dish", "Sauce", "Topping", "Drink"]

    for name in categories:
        if not FoodCategory.query.filter_by(name=name).first():
            db.session.add(FoodCategory(name=name))

    db.session.commit()

@app.route("/admin/admin_orders")
def admin_orders():
    admin = require_admin()
    orders = Order.query.all()

    return render_template(
        "admin/admin_orders.html",
        admin=admin,
        orders=orders
    )

@app.route("/admin/admin_user/<int:user_id>/toggle")
def admin_toggle_user(user_id):
    admin = require_admin()

    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()

    return redirect(url_for("admin_users"))

@app.route("/admin/admin_food/<int:food_id>/delete")
def admin_delete_food(food_id):
    admin = require_admin()

    food = Food.query.get_or_404(food_id)
    db.session.delete(food)
    db.session.commit()

    return redirect(url_for("admin_foods"))

@app.route("/admin/admin_food/<int:food_id>/toggle")
def admin_toggle_food(food_id):
    admin = require_admin()

    food = Food.query.get_or_404(food_id)
    food.availability = not food.availability
    db.session.commit()

    return redirect(url_for("admin_foods"))

@app.route("/admin/admin_order/<int:order_id>/status", methods=["POST"])
def admin_update_order_status(order_id):
    admin = require_admin()

    order = Order.query.get_or_404(order_id)
    order.status = request.form["status"]
    db.session.commit()

    return redirect(url_for("admin_orders"))

@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
def admin_delete_user(user_id):
    admin = require_admin()

    user = User.query.get_or_404(user_id)

    # Prevent deleting another admin (or yourself)
    if user.role == "admin":
        flash("You cannot delete an admin account", "danger")
        return redirect(url_for("admin_users"))

    db.session.delete(user)
    db.session.commit()

    flash("User deleted successfully", "success")
    return redirect(url_for("admin_users"))



def require_vendor():
    if  not current_user.is_authenticated:
        abort(401)

    if current_user.role != "vendor":
        abort(403)

    return current_user

def require_admin():
    if not current_user.is_authenticated:
        abort(401)

    if current_user.role != "admin":
        abort(403)

    return current_user


# DB Init
#with app.app_context():
#    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
