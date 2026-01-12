from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-key"  # temporary, will improve later

# LANDING PAGE
@app.route("/")
def landing_page():
    return render_template("index.html")


# STUDENT REGISTRATION
@app.route("/student/register", methods=["GET", "POST"])
def stud_reg():
    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        # DATABASE LOGIC WILL COME LATER
        print(full_name, email, password_hash)

        return redirect(url_for("stud_log"))

    return render_template("stud_reg.html")


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
    if "student" not in session:
        return redirect(url_for("stud_log"))
    return render_template("studash.html")


# LOGOUT
@app.route("/student/logout")
def student_logout():
    session.pop("student", None)
    return redirect(url_for("landing_page"))


if __name__ == "__main__":
    app.run(debug=True)

