import os
import sqlite3, re


from flask import Flask, render_template, request, redirect, flash, session, url_for
from flask_mail import Mail, Message
import smtplib
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config["SECRET_KEY"] = "as123124knbsdf23b2342k312"


db = sqlite3.connect("commune.db", check_same_thread=False)
db.row_factory = sqlite3.Row
cur = db.cursor()

@app.route("/")
def index():

    if not session:
        return render_template("index.html")
    family_check = cur.execute("SELECT extended_family_id FROM members WHERE id = ?", (session['user_id'],)).fetchall()[0][0]
    print(family_check)
    return redirect(url_for('home', family_id=str(family_check)))   

@app.route("/home/<family_id>", methods=["POST", "GET"])
def home(family_id):
    if family_id is None:
        return render_template("home.html")    
    else:
        family = cur.execute("SELECT *, datetime(registration_date) FROM extended_families WHERE id = ?", (family_id)).fetchall()[0]
        member_count = cur.execute("SELECT COUNT(extended_family_id) FROM members WHERE extended_family_id = ?", family_id).fetchall()[0][0]
        date = (datetime.strptime(family["datetime(registration_date)"], '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)).date()
        return render_template("family.html", family=family, member_count=member_count, date=date)
    
        
         

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        errors = {}
        reg_email = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        reg_password = r"(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-z\d]{6,12}"                                                  
        if not request.form.get("name"):
            errors["first-name"] = "First Name is Required"
        if not request.form.get("last-name"):
            errors["last-name"] = "Last Name is Required"
        if request.form.get("birth-date") > str(datetime.today()):
            errors["birth-date"] = "Birth Date is Invalid"
        if not request.form.get("birth-date"):
            errors["birth-date"] = "Birth Date is Required"
        username_check = cur.execute("SELECT * FROM members WHERE login_name = ?", [request.form.get("login-name")]).fetchall()
        if username_check:
            errors["login-name"] = "Username is already taken"
        for i in range(len(request.form.get("login-name")) - 2):
            if request.form.get("login-name")[i] == " ":
                errors["login-name"] = "No Spaces are allowed in Username"
        if not request.form.get("login-name"):
            errors["login-name"] = "Username is Required"
        email_check = cur.execute("SELECT * FROM members WHERE email = ?", [request.form.get("email")]).fetchall()
        if email_check:
            errors["email"] = "Email is already registered"
        if not re.fullmatch(reg_email, request.form.get("email")):
            errors["email"] = "Invaild Email"
        if not request.form.get("email"):
            errors["email"] = "Email is Required"
        if request.form.get("password-confirmation") != request.form.get("password"):
            errors["password"] = "Passwords do not match"
        if not re.fullmatch(reg_password, request.form.get("password")):
            errors["password"] = "Password must contain at least one of each following: letter (a-z), capital letter (A-Z), digit (0-9) and between 6-12 characters long "
        if not request.form.get("password"):
            errors["password"] = "Password is Required"
        if not errors:
            print("success")

            
            session["form"] = request.form
            print(session["form"])
            token = send_email()
            print(token)
            session["token"] = token
            return render_template("verify_email.html")


            



            
            # return redirect("/")
            # print(session["user_id"])        
        else:    
            return render_template("register.html", form=request.form, errors=errors)
    else:
        errors = {}
        form = {}
        return render_template("register.html", form=form, errors=errors)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        errors = {}
        if not request.form.get("password"):
            errors["login"] = "Please enter your password to login"
        if not request.form.get("email") and not request.form.get("login-name"):
            errors["login"] = "Please submit email or username to login"
        if not errors:
            # If user entered username to login
            if request.form.get("login-name"):
                try:
                    user = (cur.execute("SELECT * FROM members WHERE login_name = ?", [request.form.get("login-name")]).fetchall())[0]
                except:
                    errors["login"] = "Username Not Found"
                    return render_template("login.html", errors=errors, form=request.form)
                if check_password_hash(user["password_hash"], request.form.get("password")):
                    session["user_id"] = user["id"]
                    print(session["user_id"])
                    return redirect("/")
                else:
                    errors["login"] = "Username/Email or Password is Incorrect"
                    return render_template("login.html", errors=errors, form=request.form)

            # If user entered email to login
            if request.form.get("email"):
                try:
                    user = (cur.execute("SELECT * FROM members WHERE email = ?", [request.form.get("email")]).fetchall())[0]
                except:
                    errors["login"] = "Email Not Found"
                    return render_template("login.html", errors=errors, form=request.form)

                if check_password_hash(user["password_hash"], request.form.get("password")):
                    session["user_id"] = user["id"]
                    print(session["user_id"])
                    return redirect("/")
                else:
                    errors["login"] = "Username/Email or Password is Incorrect"
                    return render_template("login.html", errors=errors, form=request.form)
                
        else:

            return render_template("login.html", errors=errors, form=request.form)
    else:
        errors = {}
        form = {}
        return render_template("login.html", errors=errors, form=form)    

    
@app.route("/send_email", methods=["GET", "POST"])
def send_email():
    
        token = random.randint(9999, 99999)
        msg = EmailMessage()
        msg["Subject"] = "Confirm your email to get registered at COMMUNE !"
        msg["From"] = "mguzelkaralar@hotmail.com"
        msg["To"] = ["mguzelkaralar@hotmail.com"]
        mail_out = render_template("mailout.html", token=token)
    
        msg.add_alternative(mail_out, subtype="html")
        
        server = smtplib.SMTP("smtp.office365.com", 587)
        server.starttls()
        server.login("mguzelkaralar@hotmail.com", "mM86974299")
        # server.sendmail("mguzelkaralar@hotmail.com", "mguzelkaralar@hotmail.com", "asdasd")
        server.send_message(msg)
        

        print("email sent")

        return token

@app.route("/complete-registration", methods=["GET", "POST"])
def verify_email():
    if request.method == "POST":

    
        if int(request.form.get("verification-code")) == session["token"]:
            print("reg success")
            print(session["token"])
            print(request.form.get("verification-code"))
            print(session["form"])
            # REGISTER USER !!!
            form = session["form"]
            login_name = (form["login-name"]).rstrip()
            cur.execute("INSERT INTO members (name, last_name, birth_date, login_name, email, password_hash, living, registration_date) VALUES (?, ?, ?, ?, ?, ?, 'TRUE', julianday('now'))",
                        (form['name'], form['last-name'], form['birth-date'], login_name, form['email'], generate_password_hash(form['password'])))
            session["user_id"] = cur.execute("SELECT id FROM members WHERE login_name = ?", [login_name]).fetchall()[0][0]
            db.commit()
            session["form"] = ""           
            return redirect("/")

        else:
            
            print(session["form"])
            print("reg fail")
            print(session["token"])
            print(request.form.get("verification-code"))
            errors = {}
            errors["email_verification_fail"] = "Incorrect Verification Code"
            return render_template("register.html", form=session["form"], errors=errors)

        
@app.route("/create-family", methods=["GET", "POST"])
def create_family():
    countries = cur.execute("SELECT country FROM countries ORDER BY country").fetchall()
    cities = cur.execute("SELECT city FROM cities ORDER BY city").fetchall()
    if request.method == "POST":
        errors = {}
        familyname_check = cur.execute("SELECT * FROM extended_families WHERE login_name = ?", [request.form.get("family-login-name")]).fetchall()
        if familyname_check:
            errors["family-login-name"] = "Family Login Name is already taken"
        if not request.form.get("family-login-name"):
            errors["family-login-name"] = "Family Login Name is Required"
        if not request.form.get("family-name"):
            errors["family-name"] = "Family Name is Required"
        if not request.form.get("country"):
            errors["country"] = "Country is required"
        if not request.form.get("city"):
            errors["city"] = "City is required"        
        if request.form.get("password-confirmation") != request.form.get("password"):
            errors["password-confirmation"] = "Passwords do not match"
        if not request.form.get("password"):
            errors["password"] = "Passwords is required"
        if not errors:
            cur.execute("INSERT INTO extended_families (name, login_name, password_hash, origin_country, origin_city, registration_date, admin1) VALUES (?, ?, ?, ?, ?, julianday('now'), ?)",
                        (request.form.get("family-name"), request.form.get("family-login-name"), generate_password_hash(request.form.get("password")), request.form.get("country"), request.form.get("city"),
                        session["user_id"]))
            
                        
            cur.execute("UPDATE members SET extended_family_id = ? WHERE id = ?", (cur.execute("SELECT id FROM extended_families WHERE admin1 = ?", (session["user_id"],)).fetchall()[0][0], session["user_id"]))
            db.commit()
            
            return redirect("/")
        else:
            return render_template("create_family.html", errors=errors, form=request.form, countries=countries, cities=cities)
    else:
        errors = {}
        form = {}
        return render_template("create_family.html", errors = errors, form = form, countries=countries, cities=cities)
    

if __name__ == "__main__":
    app.run(port=8000, debug=True)