from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Food
import os


app = Flask(__name__)
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

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================
# HELPERS
# =========================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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

        return redirect(url_for("food_setup"))

    return render_template("vendor_reg.html")


# Vendor food setup
@app.route("/vendor/food_setup", methods=["GET", "POST"])
def food_setup():
    if request.method == "POST":
        # food logic comes next
        return redirect(url_for("vendor_dashboard"))

    return render_template("food_setup.html")


# Vendor dashboard
@app.route("/vendor/dashboard")
def vendor_dashboard():
    return render_template("vendor/vendor_dashboard.html")


# Login applies to both student and vendor
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["role"] = user.role

            if user.role == "vendor":
                return redirect(url_for("vendor_dashboard"))
            else:
                return redirect(url_for("studash"))

    return render_template("login.html")


# Student dashboard
@app.route("/student/dashboard")
def studash():
    return render_template("studash.html")


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing_page"))

# Vendor menu
@app.route("/vendor/vendor_menu")
def vendor_menu():
    user = require_vendor()
    foods = Food.query.filter_by(vendor_id=user.id).all()
    return render_template(
            "vendor/vendor_menu.html",
            vendor=user,
            foods=foods
        )

@app.route("/vendor/vendor_orders")
def vendor_orders():
    user = require_vendor()
    return render_template("vendor/vendor_orders.html", vendor=user)

@app.route("/vendor/settings", methods=["GET", "POST"])
def vendor_settings():
    user = require_vendor()

    if request.method == "POST":
        user.business_name = request.form["business_name"]
        user.phone = request.form["phone"]
        db.session.commit()

    return render_template("vendor/vendor_settings.html", vendor=user)

def require_vendor():
    if "user_id" not in session:
        abort(401)

    user = User.query.get(session["user_id"])

    if not user or user.role != "vendor":
        abort(403)

    return user
def require_vendor():
    if "user_id" not in session:
        abort(401)

    user = User.query.get(session["user_id"])

    if not user or user.role != "vendor":
        abort(403)

    return user

# =========================
# DB INIT
# =========================
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
