from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename 
from flask_sqlalchemy import SQLAlchemy
from models import db, User
import os


app = Flask(__name__)
app.secret_key = "dev-secret-key"  # temporary, will improve later

UPLOAD_FOLDER = 'static/uploads/vendor_logos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ocfods.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False
db.init_app(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# LANDING PAGE
@app.route("/")
def landing_page():
    return render_template("index.html")


# STUDENT REGISTRATION
@app.route("/register/student", methods=["GET", "POST"])
def stud_reg():
    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        # DATABASE LOGIC WILL COME LATER
        print(full_name, email, password_hash)

        return redirect(url_for("login"))

    return render_template("stud_reg.html")

#VENDOR REGISTRATION
@app.route("/register/vendor", methods=["GET", "POST"])
def vendor_reg():
    if request.method == "POST":
        business_name = request.form.get("business_name")
        email = request.form.get("email")
        password = request.form.get("password")

        password_hash = generate_password_hash(password)
        
        logo = request.files.get('logo')
        logo_filename = None

        if logo and allowed_file(logo.filename):
            filename = secure_filename(logo.filename)
            logo_filename = f"{email}_{filename}"
            logo.save(os.path.join(app.config['UPLOAD_FOLDER'], logo_filename))

        # DATABASE LOGIC WILL COME LATER
        vendor = User(
            role="vendor",
            business_name=business_name,
            email=email,
            password=password_hash,
            logo=logo_filename
        )

        db.session.add(vendor)
        db.session.commit()


        
        return redirect(url_for('food_setup'))
    return render_template("vendor_reg.html")

@app.route('/vendor/food_setup', methods=['GET', 'POST'])
def food_setup():
    if request.method == 'POST':
        main_dishes = request.form.getlist('main_dish[]')
        custom_main = request.form.get('custom_main_dish')

        sauces = request.form.getlist('sauce[]')
        custom_sauce = request.form.get('custom_sauce')
        # handle food items here
        return redirect(url_for('vendor_dashboard'))

    return render_template('food_setup.html')

@app.route('/vendor/dashboard', methods = ['GET', 'POST'])
def vendor_dashboard():
    #if "vendor_id" not in session:
        #return redirect(url_for("login"))
    
    #vendor_id = session["vendor_id"]
    #menu_items = MenuItem.query.filter_by(vendor_id=vendor_id).all()
    return render_template('vendor_dashboard.html')



# STUDENT LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # TEMPORARY AUTH CHECK (DB LATER)
        if email == "test@student.com" and password == "1234":
            session["student"] = email
            return redirect(url_for("studash"))

    return render_template("login.html")


# STUDENT DASHBOARD
@app.route("/student/dashboard")
def studash():
    
    return render_template("studash.html")


# LOGOUT
@app.route("/student/logout")
def student_logout():
    session.pop("student", None)
    return redirect(url_for("landing_page"))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == "__main__":
    app.run(debug=True)

