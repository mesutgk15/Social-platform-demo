import os
import sqlite3, re



from flask import Flask, render_template, request, redirect, flash, session, url_for, json, jsonify
from flask_session import Session
from flask_mail import Mail, Message
import smtplib
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random, time
from helpers import date, allowed_file, time_filter


app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config["SECRET_KEY"] = "as123124knbsdf23b2342k312"

app.jinja_env.filters['date'] = date
app.jinja_env.filters['time'] = time_filter

UPLOAD_FOLDER = "static/profile_pictures/"


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


db = sqlite3.connect("commune.db", check_same_thread=False)
db.row_factory = sqlite3.Row
cur = db.cursor()

@app.after_request
def after_request(response):
    # Ensure responses aren't cached
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():

    if not session:
        return render_template("index.html")
    family_check = cur.execute("SELECT extended_family_id FROM members WHERE id = ?", (session['user_id'],)).fetchall()[0][0]
    try:
        if family_check == session["family_id"]:
            print(family_check)
            return redirect(url_for('home', family_id=str(family_check)))
        else:
            return render_template("home.html", family_id=str(family_check))    
    except:
        return render_template("index.html")

@app.context_processor
def handle_context():
    return dict(os=os)


@app.route("/home/<family_id>", methods=["POST", "GET"])
def home(family_id):
    if family_id == "None":
        return render_template("home.html")    
    else:
        family = cur.execute("SELECT *, datetime(registration_date) FROM extended_families WHERE id = ?", (family_id)).fetchall()[0]
        member_count = cur.execute("SELECT COUNT(extended_family_id) FROM members WHERE extended_family_id = ?", family_id).fetchall()[0][0]
        date = (datetime.strptime(family["datetime(registration_date)"], '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)).date()
        return render_template("family.html", family=family, member_count=member_count, date=date)

@app.route("/home/family/list", methods=["GET", "POST"])
def family_list():
    family_members = cur.execute("SELECT id, name, last_name, birth_date, datetime(registration_date) FROM members WHERE extended_family_id = ?", (session["family_id"],))
    return render_template("family_list.html", family_members=family_members)

@app.route("/home/family/list/contact_details", methods=["POST", "GET"])
def family_member_contact():    
    print(request.args.get('id'))
    contact = cur.execute("SELECT *, datetime(registration_date) FROM members WHERE id = ?", (request.args.get('id'),))
    return render_template("family_member_contact.html", contact=contact)

@app.route("/wall", methods=["POST", "GET"])
def wall():
    if request.method == "POST":
        cur.execute("INSERT INTO posts (extended_family_id, author, content, timestamp) VALUES(?, ?, ?, julianday('now'))", ((session["family_id"]), (session["user_id"]), request.form.get("postContent")))
        db.commit()
        return redirect("/wall")
    else:
        posts = cur.execute("SELECT *, datetime(timestamp) FROM posts WHERE extended_family_id = ? ORDER BY timestamp DESC", (session["family_id"],)).fetchall()
        dictrows = [dict(row) for row in posts]
        for r in dictrows:
            r["like-count"] = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike = 'LIKE'", (r["id"],)).fetchall()[0][0]
            r["dislike-count"] = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike = 'DISLIKE'", (r["id"],)).fetchall()[0][0]
            try:
                r["like-status"] = cur.execute("SELECT like_dislike FROM likes WHERE post_id = ? AND user_id = ?", (r["id"], session["user_id"])).fetchall()[0][0]
            except:
                r["like-status"] = None
            r["author-name"] = cur.execute("SELECT name FROM members WHERE id =?", (r["author"],)).fetchall()[0][0]
            r["author-lastName"] = cur.execute("SELECT last_name FROM members WHERE id =?", (r["author"],)).fetchall()[0][0]

        
        return render_template("wall.html", posts=dictrows)

@app.route("/update-likes/")
def update_likes():
    post_id = request.args.get('post-id')
    print(request.args.get('like_dislike'))
    if request.args.get('like_dislike') == 'like':        
        try:
            if cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0] == "LIKE":
                cur.execute("UPDATE likes SET like_dislike = ?, timestamp = julianday('now') WHERE user_id = ? AND post_id = ?", (None, session["user_id"], post_id))
                db.commit()
                like_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='LIKE'", (post_id,)).fetchall()[0][0]
                dislike_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='DISLIKE'", (post_id,)).fetchall()[0][0]
                like_status = cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0]
                data = {'like_count': like_count, 
                        'dislike_count': dislike_count,
                        'like_status': like_status,
                        }
                print("a")
                return jsonify(data)
            elif cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0] == "DISLIKE" or \
            cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0] == None:
                cur.execute("UPDATE likes SET like_dislike = 'LIKE', timestamp = julianday('now') WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id))
                db.commit()
                like_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='LIKE'", (post_id,)).fetchall()[0][0]
                dislike_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='DISLIKE'", (post_id,)).fetchall()[0][0]
                like_status = cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0]
                data = {'like_count': like_count, 
                        'dislike_count': dislike_count,
                        'like_status': like_status,
                        } 
                print("b")
                return jsonify(data)
        except:
            try:
                if cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0]:
                    like_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='LIKE'", (post_id,)).fetchall()[0][0] 
                    return jsonify(like_count), 400
            except:
                cur.execute("INSERT INTO likes (post_id, user_id, like_dislike, timestamp) VALUES (?, ?, 'LIKE', julianday('now'))", (post_id, session["user_id"]))
                db.commit()
                print("c")
                like_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='LIKE'", (post_id,)).fetchall()[0][0]
                dislike_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='DISLIKE'", (post_id,)).fetchall()[0][0]      
                like_status = cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0]          
                data = {'like_count': like_count, 
                        'dislike_count': dislike_count,
                        'like_status': like_status,
                        } 
                print(like_count) 
                return jsonify(data)

        
    else:
        try:
            if cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0] == "DISLIKE":
                cur.execute("UPDATE likes SET like_dislike = ?, timestamp = julianday('now') WHERE user_id = ? AND post_id = ?", (None, session["user_id"], post_id))
                db.commit()
                dislike_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='DISLIKE'", (post_id,)).fetchall()[0][0]
                like_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='LIKE'", (post_id,)).fetchall()[0][0]
                like_status = cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0]
                data = {'like_count': like_count, 
                        'dislike_count': dislike_count,
                        'like_status': like_status,
                        }                 
                print("a")
                return jsonify(data)
            elif cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0] == "LIKE" or \
            cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0] == None:
                cur.execute("UPDATE likes SET like_dislike = 'DISLIKE', timestamp = julianday('now') WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id))
                db.commit()
                dislike_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='DISLIKE'", (post_id,)).fetchall()[0][0]
                like_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='LIKE'", (post_id,)).fetchall()[0][0]
                like_status = cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0]
                data = {'like_count': like_count, 
                        'dislike_count': dislike_count,
                        'like_status': like_status,
                        }            
                print("b")
                return jsonify(data)
        except:
            try:
                if cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0]:
                    dislike_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='DISLIKE'", (post_id,)).fetchall()[0][0] 
                    return jsonify(dislike_count), 400
            except:
                cur.execute("INSERT INTO likes (post_id, user_id, like_dislike, timestamp) VALUES (?, ?, 'DISLIKE', julianday('now'))", (post_id, session["user_id"]))
                db.commit()
                print("c")
                dislike_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='DISLIKE'", (post_id,)).fetchall()[0][0]
                like_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='LIKE'", (post_id,)).fetchall()[0][0]
                like_status = cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0]
                data = {'like_count': like_count, 
                        'dislike_count': dislike_count,
                        'like_status': like_status,
                        }            
                print(dislike_count) 
                return jsonify(data)
            

@app.route("/polls", methods=["POST", "GET"])
def polls():
    if request.method == "POST":
        poll_id = request.args.get("poll_id")
        selected_option = (request.form.getlist("poll"+poll_id))

        polls = cur.execute("SELECT *, datetime(expires_on) FROM polls WHERE extended_family_id = ?", (session["family_id"],)).fetchall()
        
        poll_dict = [dict(row) for row in polls]

        # Get creator name and last name from members table
        for i in range(len(polls)):
            voters_raw = cur.execute("SELECT COUNT(*) FROM votes WHERE poll_id = ? GROUP BY user_id", (polls[i]["id"],)).fetchall()
            voters = len(voters_raw)
            creator_last_name = cur.execute("SELECT last_name FROM members WHERE id = ?", (polls[i]["creator"],)).fetchall()[0][0]            
            poll_dict[i]["voters"] = voters
            poll_dict[i]["creator_name"] = creator_name
            poll_dict[i]["creator_last_name"] = creator_last_name

        vote_check = cur.execute("SELECT * FROM votes WHERE poll_id = ? AND user_id = ?", (poll_id, session["user_id"])).fetchall()
        last_date = cur.execute("SELECT datetime(expires_on) FROM polls WHERE id = ?", poll_id).fetchall()[0][0]

        member_count = cur.execute("SELECT COUNT(extended_family_id) FROM members WHERE extended_family_id = ?", (session["family_id"],)).fetchall()[0][0]

        if str(datetime.today()) > last_date:
            flash("Poll Expired")
            return render_template("polls.html", polls=poll_dict, member_count=member_count)
        if vote_check:
            flash("You already voted for this poll")
            return render_template("polls.html", polls=poll_dict, member_count=member_count)
        else:
            for i in range(len(selected_option)):                
                cur.execute("INSERT INTO votes (poll_id, selection_id, user_id) VALUES(?, ? ,?)", (poll_id, selected_option[i], session["user_id"]))
                db.commit()    
        
        print(selected_option)
        return redirect("/polls")
    else:
        polls = cur.execute("SELECT *, datetime(expires_on) FROM polls WHERE extended_family_id = ?", (session["family_id"],)).fetchall()
        
        poll_dict = [dict(row) for row in polls]

        # Get creator name and last name from members table
        for i in range(len(polls)):
            voters_raw = cur.execute("SELECT COUNT(*) FROM votes WHERE poll_id = ? GROUP BY user_id", (polls[i]["id"],)).fetchall()
            voters = len(voters_raw)
            creator_name = cur.execute("SELECT name FROM members WHERE id = ?", (polls[i]["creator"],)).fetchall()[0][0]
            creator_last_name = cur.execute("SELECT last_name FROM members WHERE id = ?", (polls[i]["creator"],)).fetchall()[0][0]
            poll_dict[i]["voters"] = voters            
            poll_dict[i]["creator_name"] = creator_name
            poll_dict[i]["creator_last_name"] = creator_last_name

        member_count = cur.execute("SELECT COUNT(extended_family_id) FROM members WHERE extended_family_id = ?", (session["family_id"],)).fetchall()[0][0]
                    
        return render_template("polls.html", polls=poll_dict, member_count=member_count)


@app.route("/get_selections/", methods=["POST", "GET"])
def get_selections():
    selections = {}
    
    poll_id = request.args.get("poll_id")
    i = 1
    while True:        
        try:
            selection = cur.execute("SELECT selection"+str(i)+" FROM polls WHERE id = ?", poll_id).fetchall()[0][0]
            if selection:
                selections["selection"+str(i)] = selection
                selections["selection"+str(i)+"_voteCount"] = cur.execute("SELECT COUNT(*) FROM votes WHERE poll_id = ? AND selection_id = ?", (poll_id, "selection"+str(i)+"")).fetchall()[0][0]
                selections["selection"+str(i)+"_voteTotal"] = cur.execute("SELECT COUNT(*) FROM votes WHERE poll_id = ?", (poll_id)).fetchall()[0][0]
 
            i += 1
        except:
            break
        
                
    
    print(selections)
    
    return jsonify(selections) 
    

@app.route("/start_poll", methods=["POST", "GET"])
def start_poll():
    if request.method == "POST":
        selections = []
        for i in range(24):
            slct = "selection-" + str(i)
            if request.form.get(slct):
                selections.append(request.form.get(slct))
        if not request.form.get("question"):
            flash("Type a Question")
            return render_template("start-poll.html", form=request.form, selections=selections)
        if str(datetime.today()) > request.form.get("last_date"):
            flash("Invalid Due Date for Poll Ending")
            return render_template("start-poll.html", form=request.form, selections=selections)
        if len(selections) < 2:
            flash("Type at Least 2 Selections")
            return render_template("start-poll.html", form=request.form, selections=selections)
        if int(request.form.get("max_selection")) < 1 or (int(request.form.get("max_selection")) >= len(selections)):
            flash("Invalid Max. Selection")
            return render_template("start-poll.html", form=request.form, selections=selections)

        cur.execute("INSERT INTO polls (extended_family_id, question, max_selection, expires_on, creator) VALUES(?, ?, ?, ?, ?)", (session["family_id"], request.form.get("question"),
                    request.form.get("max_selection"), request.form.get("last_date"), session["user_id"]))
                    
        creator = cur.execute("SELECT name, last_name FROM members WHERE id = ?", (session["user_id"],)).fetchall()
        

        cur.execute("INSERT INTO posts (extended_family_id, author, content, timestamp) VALUES(?, 1, ?, julianday('now'))", (session["family_id"], ""+str(creator[0]["name"])+" "+str(creator[0]["last_name"])+" has started a new poll. Last Date to vote is: "+request.form.get("last_date")+""))

        db.commit()

        poll_id = cur.lastrowid
        print(poll_id)


        
        print(len(selections))
        columns = []
        columns_id = []
        for i in range(len(selections)):
            columns.append("selection"+str(i+1))
            columns_id.append("selection"+str(i+1)+"_id")

        for i in range(len(selections)):
            cur.execute("UPDATE polls SET "+columns[i]+" = ?, "+columns_id[i]+" = ? WHERE id = ?", (selections[i], i+1, poll_id))
            db.commit()

        return redirect("/polls")            
    else:
        form = {} 
        selections = []
        return render_template("start-poll.html", form=form, selections=selections)



@app.route("/leave_family", methods=["POST", "GET"])
def leave_family():
    cur.execute("UPDATE members SET extended_family_id = ? WHERE id = ?", (None, session["user_id"]))
    db.commit()
    session["family_id"] = ""
    return redirect("/")
        
         

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
                    session["username"] = user["login_name"]
                    session["family_id"] = user["extended_family_id"]
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
                    session["username"] = user["login_name"]
                    session["family_id"] = user["extended_family_id"]
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
            session["username"] = cur.execute("SELECT login_name FROM members WHERE id = ?", (session["user_id"],)).fetchall()[0][0]
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
            session["family_id"] = cur.execute("SELECT extended_family_id FROM members WHERE id = ?", (session["user_id"],)).fetchall()[0][0]
            db.commit()
            
            return redirect("/")
        else:
            return render_template("create_family.html", errors=errors, form=request.form, countries=countries)
    else:
        errors = {}
        form = {}
        return render_template("create_family.html", errors = errors, form = form, countries=countries)
    
@app.route("/join_family", methods=["GET", "POST"])
def join_family():
    if request.method == "POST":
        form= {}
        errors= {}
        if not request.form.get("password"):
            errors["login"] = "Passwords is required"        
        if not request.form.get("family-login-name"):
            errors["login"] = "Family Login Name is Required"
        if not errors:
            try:
                family = cur.execute("SELECT * FROM extended_families WHERE login_name = ?", [request.form.get("family-login-name")]).fetchall()[0]
            except:
                errors["login"] = "Family is not found"
                return render_template("join_family.html", form=form, errors=errors)
            if not family:
                errors["login"] = "Family is not found"
            if not check_password_hash(family["password_hash"], request.form.get("password")):
                errors["login"] = "Incorrect Password"
            if not errors:
                cur.execute("UPDATE members SET extended_family_id = ? WHERE id = ?", (str(family["id"]), session["user_id"]))
                db.commit()
                session["family_id"] = family["id"]
                return redirect(url_for('index'))
            else:
                return render_template("join_family.html", form=form, errors=errors)    
        else:
            return render_template("join_family.html", form=form, errors=errors)    
        
        
    else:
        form= {}
        errors= {}
        return render_template("join_family.html", form=form, errors=errors)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    profile_data = cur.execute("SELECT *, datetime(registration_date) FROM members WHERE id = ?", (session["user_id"],))
    return render_template("profile.html", profile_data=profile_data)


@app.route("/upload_photo", methods=["GET", "POST"])
def upload_photo():
    if request.method == "POST" and request.args.get('photo') == "upload":
        file = request.files["photo"]
        if not file:
            flash("No file chosen !")
            return redirect("profile")            
        elif not allowed_file(file.filename):
            print(allowed_file(file.filename))
            flash("Only JPG and JPEG files are allowed !")
            return redirect("profile")            

        print(allowed_file(file.filename))
        filename = str((session["user_id"])) + ".jpg"
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        return redirect(url_for('profile'))
    else:
        if request.args.get('photo') == "delete":
            filename = str((session["user_id"])) + ".jpg"
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            return redirect("profile")
        else:
            return redirect("profile")

@app.route("/profile/update/", methods=["GET", "POST"])
def update_profile_info():
    if request.method == "POST" and request.args.get('update') == "address":
        cur.execute("UPDATE members SET address = ? WHERE id = ?", [request.form.get("address-text"), session["user_id"]])
        db.commit()
        return redirect("/profile")
    elif request.args.get('update') == "delete-address":
        cur.execute("UPDATE members SET address = ? WHERE id = ?",  (None, session["user_id"]))
        db.commit()
        return redirect("/profile")
    elif request.method == "POST" and request.args.get('update') == "phone_number":
        cur.execute("UPDATE members SET phone_number = ? WHERE id = ?", [request.form.get("phone_number"), session["user_id"]])
        db.commit()
        return redirect("/profile")
    elif request.args.get('update') == "delete-phone_number":
        cur.execute("UPDATE members SET phone_number = ? WHERE id = ?",  (None, session["user_id"]))
        db.commit()
        return redirect("/profile")  

@app.route("/get-city/")
def get_city():
    country = request.args.get('country')
    country_id = cur.execute("SELECT id from countries WHERE country = ?", [country]).fetchall()[0][0]
    city = cur.execute("SELECT city FROM cities WHERE country_id = ?", [country_id]).fetchall()
    cities = [dict(row) for row in city]
    print(jsonify(cities))
    return jsonify(cities)

if __name__ == "__main__":
    app.run(port=8000, debug=True, threaded=True)