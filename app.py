from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Food, Order, FoodCategory, OrderItem, Payment, Rating
from dotenv import load_dotenv
from paystackapi.transaction import Transaction
import os
from sqlalchemy import func
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import requests
from datetime import datetime
from geopy.distance import geodesic
from flask_socketio import SocketIO, emit



app = Flask(__name__)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    logger=True,
    engineio_logger=True
    )

app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

load_dotenv()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

app.config["PAYSTACK_PUBLIC_KEY"] = os.getenv("PAYSTACK_PUBLIC_KEY")
app.config["PAYSTACK_SECRET_KEY"] = os.getenv("PAYSTACK_SECRET_KEY")
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

@socketio.on("connect")
def handle_connect():
    print("VENDOR CONNECTED")

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

@app.route("/analytics")
def analytics():

    # TOTAL ORDERS
    total_orders = Order.query.filter_by(status="paid").count()

    # TOTAL REVENUE
    total_revenue = db.session.query(
        func.sum(Order.total_amount)
    ).filter(
        Order.status == "paid"
    ).scalar() or 0

    # MOST POPULAR VENDOR
    popular_vendor = db.session.query(
        User.business_name,
        func.count(Order.id).label("total_orders")
    ).join(
        Order, Order.vendor_id == User.id
    ).filter(
        Order.status == "paid"
    ).group_by(
        User.id
    ).order_by(
        func.count(Order.id).desc()
    ).first()

    # HIGHEST RATED VENDOR
    highest_rated_vendor = db.session.query(
        User.business_name,
        func.avg(Rating.rating).label("avg_rating")
    ).join(
        Rating, Rating.vendor_id == User.id
    ).group_by(
        User.id
    ).order_by(
        func.avg(Rating.rating).desc()
    ).first()

    # TOP FOODS
    top_foods = db.session.query(
        Food.name,
        func.count(OrderItem.food_id).label("total")
    ).join(
        OrderItem
    ).group_by(
        Food.id
    ).order_by(
        func.count(OrderItem.food_id).desc()
    ).limit(5).all()

    # FOOD CHART DATA
    food_chart_labels = [food.name for food in top_foods]
    food_chart_values = [food.total for food in top_foods]

    # VENDOR POPULARITY
    vendor_data = db.session.query(
        User.business_name,
        func.count(Order.id)
    ).join(
        Order, Order.vendor_id == User.id
    ).group_by(
        User.id
    ).all()

    vendor_labels = [v[0] for v in vendor_data]
    vendor_values = [v[1] for v in vendor_data]
    
    # GENERAL FOOD ANALYTICS

    general_foods = db.session.query(
        Food.name,
        func.count(OrderItem.food_id).label("total")
    ).join(
        OrderItem
    ).group_by(
        Food.id
    ).order_by(
        func.count(OrderItem.food_id).desc()
    ).limit(10).all()

    # MAIN DISH ANALYTICS

    main_foods = db.session.query(
        Food.name,
        func.count(OrderItem.food_id).label("total")
    ).join(
        OrderItem
    ).join(
        FoodCategory
    ).filter(
        FoodCategory.name == "Main Dish"
    ).group_by(
        Food.id
    ).all()

    # TOPPING ANALYTICS

    topping_foods = db.session.query(
        Food.name,
        func.count(OrderItem.food_id).label("total")
    ).join(
        OrderItem
    ).join(
        FoodCategory
    ).filter(
        FoodCategory.name == "Topping"
    ).group_by(
        Food.id
    ).all()

    # DRINK ANALYTICS

    drink_foods = db.session.query(
        Food.name,
        func.count(OrderItem.food_id).label("total")
    ).join(
        OrderItem
    ).join(
        FoodCategory
    ).filter(
        FoodCategory.name == "Drink"
    ).group_by(
        Food.id
    ).all()

    general_labels = [f.name for f in general_foods]
    general_values = [f.total for f in general_foods]

    main_labels = [f.name for f in main_foods]
    main_values = [f.total for f in main_foods]

    topping_labels = [f.name for f in topping_foods]
    topping_values = [f.total for f in topping_foods]

    drink_labels = [f.name for f in drink_foods]
    drink_values = [f.total for f in drink_foods]

    return render_template(
        "analytics.html",

        total_orders=total_orders,
        total_revenue=total_revenue,

        popular_vendor=popular_vendor,
        highest_rated_vendor=highest_rated_vendor,

        food_chart_labels=food_chart_labels,
        food_chart_values=food_chart_values,

        vendor_labels=vendor_labels,
        vendor_values=vendor_values,

        general_labels=general_labels,
        general_values=general_values,

        main_labels=main_labels,
        main_values=main_values,

        topping_labels=topping_labels,
        topping_values=topping_values,

        drink_labels=drink_labels,
        drink_values=drink_values,

        top_foods=top_foods
    )

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

    pending_orders = Order.query.filter_by(
        vendor_id=current_user.id,
        status="paid"
    ).order_by(Order.order_date.desc()).all()

    menu_items = Food.query.filter_by(
        vendor_id=current_user.id
    ).all()

    return render_template(
        "vendor/vendor_dashboard.html",
        vendor=current_user,
        pending_orders=pending_orders,
        menu_items=menu_items
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
@login_required
def studash():
    if current_user.role != "student":
        abort(403)

    vendors = User.query.filter_by(role="vendor", is_active=True).all()

    for vendor in vendors:
        avg_rating, rating_count = (
            db.session.query(
                func.avg(Rating.rating),
                func.count(Rating.id)
            )
            .filter(Rating.vendor_id == vendor.id)
            .first()
        )

        vendor.avg_rating = avg_rating or 0
        vendor.rating_count = rating_count or 0

    rate_order = request.args.get("rate_order")
    unrated_orders = Order.query.filter(
        Order.customer_id == current_user.id,
        Order.status == "paid",
        ~Order.id.in_(
            db.session.query(Rating.order_id)
        )
    ).all()

    return render_template(
        "student/studash.html",
        vendors=vendors,
        rate_order=rate_order,
        unrated_orders=unrated_orders
    )

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

@app.route("/student/orders")
@login_required
def student_orders():
    orders = Order.query.filter_by(customer_id=current_user.id).all()
    return render_template("student/stu_orders.html", orders=orders)

@app.route("/student/dashboard/<int:vendor_id>/menu")
@login_required
def stud_vend_menu(vendor_id):
    if current_user.role != "student":
        abort(403)

    vendor = User.query.filter_by(id=vendor_id, role="vendor", is_active=True).first_or_404()

    foods = Food.query.filter_by(
        vendor_id=vendor.id,
        availability=True
    ).all()

    return render_template(
        "student/stu_vend_menu.html",
        vendor=vendor,
        foods=foods
    )

@app.route("/order/place", methods=["POST"])
@login_required
def place_order():
    if current_user.role != "student":
        abort(403)

    food_ids = request.form.getlist("food_ids")
    vendor_id = request.form.get("vendor_id")
    
    if not food_ids:
        flash("Please select at least one food item", "warning")
        return redirect(request.referrer)
    
    foods = Food.query.filter(Food.id.in_(food_ids)).all()
    
    
    subtotal = sum(food.price for food in foods)


    customer_latitude = request.form.get("customer_latitude")
    customer_longitude = request.form.get("customer_longitude")
    vendor = User.query.get(vendor_id)
    #vendor coordinates
    vendor_coords = (vendor.latitude, vendor.longitude)
    
    #customer coordinates
    customer_coords = ( customer_latitude, customer_longitude)

    #calculate distance
    distance_km = geodesic(vendor_coords, customer_coords).km

    # Calculate transportation fee
    transportation_fee = distance_km * vendor.delivery_fee_km
    
    total = subtotal + transportation_fee

    return render_template(
        "student/order_review.html",
        foods=foods,
        subtotal=subtotal,
        transportation_fee=transportation_fee,
        total=total
    )

@app.route("/order/confirm", methods=["POST"])
@login_required
def confirm_order():
    if current_user.role != "student":
        abort(403)

    food_ids = request.form.getlist("food_ids")
    foods = Food.query.filter(Food.id.in_(food_ids)).all()

    if not foods:
        abort(400)

    vendor_id = foods[0].vendor_id
    vendor = User.query.get(vendor_id)

    subtotal = sum(food.price for food in foods)

    customer_latitude = request.form.get("customer_latitude")
    customer_longitude = request.form.get("customer_longitude")

    #vendor coordinates
    vendor_coords = (vendor.latitude, vendor.longitude)
    
    #customer coordinates
    customer_coords = ( customer_latitude, customer_longitude)

    #calculate distance
    distance_km = geodesic(vendor_coords, customer_coords).km

    # Calculate transportation fee
    transportation_fee = distance_km * vendor.delivery_fee_km

    # Final total
    total_amount = subtotal + transportation_fee

    order = Order(
        customer_id=current_user.id,
        vendor_id=vendor_id,
        total_amount=total_amount,
        customer_latitude=customer_latitude,
        customer_longitude=customer_longitude,
        delivery_distance_km=distance_km,
        transportation_fee=transportation_fee, 
        status="pending"
    )

    db.session.add(order)
    db.session.flush()  # get order.id

    for food in foods:
        db.session.add(OrderItem(
            order_id=order.id,
            food_id=food.id,
            quantity=1,
            subtotal=food.price
        ))

    db.session.commit()

    return redirect(url_for("payment_page", order_id=order.id))

@app.route("/payment/<int:order_id>")
@login_required
def payment_page(order_id):
    order = Order.query.get_or_404(order_id)

    if order.customer_id != current_user.id:
        abort(403)

    return render_template("student/payment_page.html", order=order)

@app.route("/payment/initiate/<int:order_id>")
@login_required
def initiate_payment(order_id):
    order = Order.query.get_or_404(order_id)

    # defing callback and test
    url = "https://api.paystack.co/transaction/initialize"
    
    headers = {
        "Authorization": f"Bearer {app.config['PAYSTACK_SECRET_KEY']}",
        "Content-Type": "application/json"
    }

    data = {
        "email": current_user.email,
        "amount": int(order.total_amount * 100),
        "reference": f"ORD_{order.id}_{int(datetime.now().timestamp())}", 
        "callback_url": url_for("verify_payment", _external=True),
        "metadata": {
            "order_id": str(order.id), 
            "user_id": str(current_user.id)
        }
    }

    response = requests.post(url, json=data, headers=headers)
    res = response.json()

    if res["status"]:
        return redirect(res["data"]["authorization_url"])

    flash("Payment initialization failed", "danger")
    return redirect(url_for("studash"))

def generate_receipt(order):
    # Folder to save receipts
    receipt_folder = os.path.join("static", "receipts")
    os.makedirs(receipt_folder, exist_ok=True)

    filename = f"receipt_{order.id}.pdf"
    filepath = os.path.join(receipt_folder, filename)

    # Create PDF
    doc = SimpleDocTemplate(filepath)
    styles = getSampleStyleSheet()

    elements = []

    # title
    elements.append(Paragraph("SEAMLESS Receipt", styles["Title"]))
    elements.append(Paragraph("Food Order Receipt", styles["Normal"]))
    elements.append(Spacer(1, 10))

    #vendor info
    vendor = order.vendor
    elements.append(Paragraph(f"Vendor: {vendor.business_name}", styles["Normal"]))

    # Vendor logo (if exists)
    if vendor.logo:
        logo_path = os.path.join("static/uploads/vendor_logos", vendor.logo)
        if os.path.exists(logo_path):
            elements.append(Image(logo_path, width=80, height=80))

    elements.append(Spacer(1, 10))

    # ORDER INFO
    elements.append(Paragraph(f"Order ID: {order.id}", styles["Normal"]))
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
    elements.append(Paragraph(f"Vendor: {order.vendor.business_name}", styles["Normal"]))
    elements.append(Paragraph(f"Transaction Ref: {getattr(order, 'transaction_ref', 'N/A')}", styles["Normal"]))    
    elements.append(Spacer(1, 10))

    # TABLE DATA
    data = [["Item", "Qty", "Price (₦)", "Subtotal (₦)"]]

    subtotal = 0

    for item in order.items:
        data.append([
            item.food.name,
            str(item.quantity),
            f"{item.food.price:.2f}",
            f"{item.subtotal:.2f}"
        ])
        subtotal += item.subtotal

    # Transport fee 
    transportation_fee = 0

    data.append(["", "", "Subtotal", f"{subtotal:.2f}"])
    data.append(["", "", "Transport", f"{transportation_fee:.2f}"])
    data.append(["", "", "Total", f"{order.total_amount:.2f}"])

    table = Table(data, hAlign="LEFT")

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    
    #FOOTER

    elements.append(Paragraph("Thank you for ordering with CampusEats!", styles["Italic"]))
    elements.append(Paragraph("Contact: support@campuseats.com", styles["Normal"]))

    doc.build(elements)

    return filename



@app.route("/payment/verify", methods=["GET"])
@app.route("/payment/verify/<reference>", methods=["GET"])
@login_required
def verify_payment(reference=None):
    if not reference:
        reference = request.args.get("reference")

    if not reference:
        flash("No payment reference found", "danger")
        return redirect(url_for("studash"))

    # Verify with Paystack
    response = Transaction.verify(reference=reference)
    if not response or not response.get("status"):
        flash("Payment verification failed", "danger")
        return redirect(url_for("studash"))

    data = response["data"]
    order_id = None
    metadata = data.get("metadata")

    # Check Metadata ---
    if isinstance(metadata, dict):
        order_id = metadata.get("order_id")
    
    # Check Reference String (ORD_22_12345) ---
    if not order_id and reference and "ORD_" in reference:
        try:
            order_id = reference.split("_")[1]
        except: pass

    # Check Referrer ---Failsafe ---
   
    if not order_id and isinstance(metadata, dict) and 'referrer' in metadata:
        try:
            referrer_url = metadata['referrer']
            # Grabs the last number in the URL (the 22)
            order_id = referrer_url.rstrip('/').split('/')[-1]
            print(f"DEBUG: Recovered Order ID {order_id} from Referrer URL")
        except: pass

    if not order_id:
        print(f"DEBUG: Still no Order ID. Data: {data}")
        flash("Transaction verified but Order ID not found", "danger")
        return redirect(url_for("studash"))



    # Finalize in Database
    order = db.session.get(Order, int(order_id))
    if not order:
        abort(404)

    reference = data["reference"]
    order.transaction_ref = reference

    if order.status != "paid":
        order.status = "paid"
        payment = Payment(order_id=order.id, payment_method="paystack", payment_status="successful")
        db.session.add(payment)
        
        receipt_file = generate_receipt(order)
        order.receipt_file = receipt_file
        db.session.commit()

        print("=======EMITTING NEW ORDER=======")
        print(order.id)
        socketio.emit(
        "new_order",
        {
            "order_id": order.id,
            "customer": order.customer.name,
            "total": order.total_amount
        }
    )

    flash("Payment successful!", "success")
    return redirect(url_for("studash", rate_order=order.id))

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

    orders = Order.query.filter(
        Order.vendor_id == user.id,
        Order.status.in_(["accepted", "ready", "delivered"])
    ).order_by(
        Order.order_date.desc()
    ).all()
    
    return render_template(
        "vendor/vendor_orders.html",
        vendor=user,
        orders=orders
    )

@app.route("/vendor/order/<int:order_id>/take", methods=["POST"])
@login_required
def take_order(order_id):

    if current_user.role != "vendor":
        abort(403)

    order = Order.query.get_or_404(order_id)

    order.status = "accepted"

    db.session.commit()

    flash(
        f"Order #{order.id} accepted successfully",
        "success"
    )

    return redirect(
        url_for("vendor_dashboard")
    )

@app.route("/vendor/order/<int:order_id>")
@login_required
def vendor_order_details(order_id):

    order = Order.query.get_or_404(order_id)

    if order.vendor_id != current_user.id:
        abort(403)

    return render_template(
        "vendor/order_details.html",
        vendor = current_user,
        order=order
    )

@app.route("/vendor/order/<int:order_id>/ready", methods=["POST"])
@login_required
def mark_ready(order_id):

    if current_user.role != "vendor":
        abort(403)

    order = Order.query.get_or_404(order_id)

    order.status = "ready"

    db.session.commit()

    flash(
        f"Order #{order.id} marked as ready",
        "success"
    )

    return redirect(
        url_for("vendor_orders")
    )

@app.route("/vendor/order/<int:order_id>/delivered", methods=["POST"])
@login_required
def mark_delivered(order_id):

    if current_user.role != "vendor":
        abort(403)

    order = Order.query.get_or_404(order_id)

    order.status = "delivered"

    db.session.commit()

    flash(
        f"Order #{order.id} delivered successfully",
        "success"
    )

    return redirect(
        url_for("vendor_orders")
    )

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
            
        # save delivery rate
        delivery_fee = request.form.get("delivery_fee_km")
        if delivery_fee:
            current_user.delivery_fee_km = float(delivery_fee)
        
        # save location
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        address = request.form.get("address")

        if latitude and longitude:
            current_user.latitude = float(latitude)
            current_user.longitude = float(longitude)

        if address:
            current_user.address = address

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

    # Prevent deleting admin 
    if user.role == "admin":
        flash("You cannot delete an admin account", "danger")
        return redirect(url_for("admin_users"))

    db.session.delete(user)
    db.session.commit()

    flash("User deleted successfully", "success")
    return redirect(url_for("admin_users"))

@app.route("/payment/callback")
def payment_callback():
    return "Verified!"

@app.route("/rate/vendor", methods=["POST"])
def submit_rating():

    order_id = request.form.get("order_id")
    rating_value = request.form.get("rating")
    comment = request.form.get("comment")

    if not rating_value:
        flash("Please select a rating", "warning")
        return redirect(url_for("studash"))

    order = Order.query.get_or_404(order_id)

    if order.customer_id != current_user.id:
        abort(403)

    existing = Rating.query.filter_by(
        user_id=current_user.id,
        order_id=order.id
    ).first()

    if existing:
        flash("You already rated this order", "info")
        return redirect(url_for("studash"))

    rating = Rating(
        user_id=current_user.id,
        vendor_id=order.vendor_id,
        order_id=order.id,
        rating=int(rating_value),
        comment=comment
    )

    db.session.add(rating)
    db.session.commit()

    flash("Thanks for your rating!", "success")
    return redirect(url_for("studash"))

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

if __name__ == "__main__":
    socketio.run(
        app,
        debug=True
    )
