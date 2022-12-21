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

# Define jinja filters to be used in html templates
app.jinja_env.filters['date'] = date
app.jinja_env.filters['time'] = time_filter

# Define the path which profile pictures will be kept.
UPLOAD_FOLDER = "static/profile_pictures/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Database connection and define cursor
def get_conn():
    db = sqlite3.connect("commune.db", check_same_thread=False)
    db.row_factory = sqlite3.Row
    return db


@app.after_request
def after_request(response):
    # Ensure responses aren't cached
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():

    # If there is no logged in user
    if not session:
        form = {}
        errors = {}
        return render_template("index.html", form=form, errors=errors)
    
    
    return redirect(url_for('home'))
    
    # Any error on family part direct to home without login
    # except:
    #     form = {}
    #     errors = {}
    #     return render_template("index.html", form=form, errors=errors)

# Convert os variables to a dict to be used in html templates. Will be used to check if user has a profile picture uploaded in relevant folder.
@app.context_processor
def handle_context():
    return dict(os=os)


@app.route("/home", methods=["POST", "GET"])
def home():
    # If there is no family id passed through url redirect to home

    try:
        family_id = session["family_id"]
        # Get family data for family's home page
        db = get_conn()
        cur = db.cursor()
        family = cur.execute("SELECT *, datetime(registration_date) FROM extended_families WHERE id = ?", (family_id,)).fetchall()[0]
        member_count = cur.execute("SELECT COUNT(extended_family_id) FROM members WHERE extended_family_id = ?", (family_id,)).fetchall()[0][0]
        db.close()
        date = (datetime.strptime(family["datetime(registration_date)"], '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)).date()
        return render_template("family.html", family=family, member_count=member_count, date=date)
    except:
        return render_template("home.html")    

@app.route("/home/family/list", methods=["GET", "POST"])
def family_list():
    # Get all family members data for family list 
    db = get_conn()
    cur = db.cursor()
    family_members = cur.execute("SELECT id, name, last_name, birth_date, datetime(registration_date) FROM members WHERE extended_family_id = ?", (session["family_id"],)).fetchall()
    db.close()
    return render_template("family_list.html", family_members=family_members)


@app.route("/home/family/list/contact_details", methods=["POST", "GET"])
def family_member_contact():    
    # Get a specific member's data for the member id passed through url. Triggered from famil list page
    db = get_conn()
    cur = db.cursor()
    contact = cur.execute("SELECT *, datetime(registration_date) FROM members WHERE id = ?", (request.args.get('id'),)).fetchall()
    db.close()
    return render_template("family_member_contact.html", contact=contact)

@app.route("/wall", methods=["POST", "GET"])
def wall():
    if request.method == "POST":
        # Insert the post into database. Post content received from the modal form popped up in html
        db = get_conn()
        cur = db.cursor()        
        cur.execute("INSERT INTO posts (extended_family_id, author, content, timestamp) VALUES(?, ?, ?, julianday('now'))", ((session["family_id"]), (session["user_id"]), request.form.get("postContent")))
        db.commit()
        db.close()
        return redirect("/wall")
    else:
        # Get all posts of the family 
        db = get_conn()
        cur = db.cursor()        
        posts = cur.execute("SELECT *, datetime(timestamp) FROM posts WHERE extended_family_id = ? ORDER BY timestamp DESC", (session["family_id"],)).fetchall()
        # Append like/dislike countts and author data to above list
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

        db.close()
        return render_template("wall.html", posts=dictrows)

@app.route("/update-likes/")
def update_likes():
    # Define post_id user liked or disliked
    post_id = request.args.get('post-id')
    if request.args.get('like_dislike') == 'like':
        db = get_conn()
        cur = db.cursor()
        # Check if user liked or disliked the post before, update likes table accordingly
        try:
            # If liked before update like status to null
            if cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0] == "LIKE":
                cur.execute("UPDATE likes SET like_dislike = ?, timestamp = julianday('now') WHERE user_id = ? AND post_id = ?", (None, session["user_id"], post_id))
                db.commit()
                # Get updated like/dislike count and return
                like_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='LIKE'", (post_id,)).fetchall()[0][0]
                dislike_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='DISLIKE'", (post_id,)).fetchall()[0][0]
                like_status = cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0]
                data = {'like_count': like_count, 
                        'dislike_count': dislike_count,
                        'like_status': like_status,
                        }
                db.close()
                return jsonify(data)

            # If disliked or null update as like
            elif cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0] == "DISLIKE" or \
            cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0] == None:
                cur.execute("UPDATE likes SET like_dislike = 'LIKE', timestamp = julianday('now') WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id))
                db.commit()
                # Get updated like/dislike count and return
                like_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='LIKE'", (post_id,)).fetchall()[0][0]
                dislike_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='DISLIKE'", (post_id,)).fetchall()[0][0]
                like_status = cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0]
                data = {'like_count': like_count, 
                        'dislike_count': dislike_count,
                        'like_status': like_status,
                        } 
                db.close()
                return jsonify(data)
        except:
            try:
                # If no dislike or like found in database, try one more time to query
                if cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0]:
                    like_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='LIKE'", (post_id,)).fetchall()[0][0] 
                    db.close()
                    return jsonify(like_count), 400
            except:
                # If no like or dislike found in db, insert new one in likes table
                cur.execute("INSERT INTO likes (post_id, user_id, like_dislike, timestamp) VALUES (?, ?, 'LIKE', julianday('now'))", (post_id, session["user_id"]))
                db.commit()
                # Get updated like/dislike count and return
                like_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='LIKE'", (post_id,)).fetchall()[0][0]
                dislike_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='DISLIKE'", (post_id,)).fetchall()[0][0]      
                like_status = cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0]          
                data = {'like_count': like_count, 
                        'dislike_count': dislike_count,
                        'like_status': like_status,
                        } 
                print(like_count)
                db.close() 
                return jsonify(data)

        
    else:
        db = get_conn()
        cur = db.cursor()
        try:
            # Check if user liked or disliked the post before, update likes table accordingly            
            if cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0] == "DISLIKE":
                # If liked before update like status to null
                cur.execute("UPDATE likes SET like_dislike = ?, timestamp = julianday('now') WHERE user_id = ? AND post_id = ?", (None, session["user_id"], post_id))
                db.commit()
                # Get updated like/dislike count and return
                dislike_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='DISLIKE'", (post_id,)).fetchall()[0][0]
                like_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='LIKE'", (post_id,)).fetchall()[0][0]
                like_status = cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0]
                data = {'like_count': like_count, 
                        'dislike_count': dislike_count,
                        'like_status': like_status,
                        }                 
                db.close()
                return jsonify(data)
            # If liked or null update as dislike
            elif cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0] == "LIKE" or \
            cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0] == None:
                cur.execute("UPDATE likes SET like_dislike = 'DISLIKE', timestamp = julianday('now') WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id))
                db.commit()
                # Get updated like/dislike count and return
                dislike_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='DISLIKE'", (post_id,)).fetchall()[0][0]
                like_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='LIKE'", (post_id,)).fetchall()[0][0]
                like_status = cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0]
                data = {'like_count': like_count, 
                        'dislike_count': dislike_count,
                        'like_status': like_status,
                        }            
                db.close()
                return jsonify(data)
        except:
            try:
                # If no dislike or like found in database, try one more time to query
                if cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0]:
                    dislike_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='DISLIKE'", (post_id,)).fetchall()[0][0]
                    db.close() 
                    return jsonify(dislike_count), 400
            except:
                # If no like or dislike found in db, insert new one in likes table
                cur.execute("INSERT INTO likes (post_id, user_id, like_dislike, timestamp) VALUES (?, ?, 'DISLIKE', julianday('now'))", (post_id, session["user_id"]))
                db.commit()
                # Get updated like/dislike count and return
                dislike_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='DISLIKE'", (post_id,)).fetchall()[0][0]
                like_count = cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = ? AND like_dislike ='LIKE'", (post_id,)).fetchall()[0][0]
                like_status = cur.execute("SELECT like_dislike FROM likes WHERE user_id = ? AND post_id = ?", (session["user_id"], post_id)).fetchall()[0][0]
                data = {'like_count': like_count, 
                        'dislike_count': dislike_count,
                        'like_status': like_status,
                        }            
                db.close() 
                return jsonify(data)
            

@app.route("/polls", methods=["POST", "GET"])
def polls():
    if request.method == "POST":
        # Vote process began. Get the selections voted and poll id user voted for. 
        poll_id = request.args.get("poll_id")
        selected_option = (request.form.getlist("poll"+poll_id))

        # Get polls from db, will be passed to html template after voting completed and redirected to polls page
        db = get_conn()
        cur = db.cursor()        
        polls = cur.execute("SELECT *, datetime(expires_on) FROM polls WHERE extended_family_id = ? ORDER BY id DESC", (session["family_id"],)).fetchall()
        
        poll_dict = [dict(row) for row in polls]

        # Get creator name and last name from members table, get voter count. append to existing polls list for all polls
        for i in range(len(polls)):
            voters_raw = cur.execute("SELECT COUNT(*) FROM votes WHERE poll_id = ? GROUP BY user_id", (polls[i]["id"],)).fetchall()
            voters = len(voters_raw)
            creator_name = cur.execute("SELECT name FROM members WHERE id = ?", (polls[i]["creator"],)).fetchall()[0][0]
            creator_last_name = cur.execute("SELECT last_name FROM members WHERE id = ?", (polls[i]["creator"],)).fetchall()[0][0]            
            poll_dict[i]["voters"] = voters
            poll_dict[i]["creator_name"] = creator_name
            poll_dict[i]["creator_last_name"] = creator_last_name

        vote_check = cur.execute("SELECT * FROM votes WHERE poll_id = ? AND user_id = ?", (poll_id, session["user_id"])).fetchall()
        last_date = cur.execute("SELECT datetime(expires_on) FROM polls WHERE id = ?", (poll_id,)).fetchall()[0][0]

        # Get family member count to calculate show voter ratio among all members
        member_count = cur.execute("SELECT COUNT(extended_family_id) FROM members WHERE extended_family_id = ?", (session["family_id"],)).fetchall()[0][0]

        if str(datetime.today()) > last_date:
            flash("Poll Expired")
            db.close()
            return render_template("polls.html", polls=poll_dict, member_count=member_count)
        if vote_check:
            flash("You already voted for this poll")
            db.close()
            return render_template("polls.html", polls=poll_dict, member_count=member_count)
        else:
            # Place votes for voted selections in database
            for i in range(len(selected_option)):                
                cur.execute("INSERT INTO votes (poll_id, selection_id, user_id) VALUES(?, ? ,?)", (poll_id, selected_option[i], session["user_id"]))
                db.commit()    
        
        db.close()
        return redirect("/polls")
    else:
        # Get all polls
        db = get_conn()
        cur = db.cursor()        
        polls = cur.execute("SELECT *, datetime(expires_on) FROM polls WHERE extended_family_id = ? ORDER BY id DESC", (session["family_id"],)).fetchall()
        
        poll_dict = [dict(row) for row in polls]

        # Get creator name and last name from members table, get voter count. append to existing polls list for all polls
        for i in range(len(polls)):
            voters_raw = cur.execute("SELECT COUNT(*) FROM votes WHERE poll_id = ? GROUP BY user_id", (polls[i]["id"],)).fetchall()
            voters = len(voters_raw)
            creator_name = cur.execute("SELECT name FROM members WHERE id = ?", (polls[i]["creator"],)).fetchall()[0][0]
            creator_last_name = cur.execute("SELECT last_name FROM members WHERE id = ?", (polls[i]["creator"],)).fetchall()[0][0]
            poll_dict[i]["voters"] = voters            
            poll_dict[i]["creator_name"] = creator_name
            poll_dict[i]["creator_last_name"] = creator_last_name

        # Get family member count to calculate show voter ratio among all members
        member_count = cur.execute("SELECT COUNT(extended_family_id) FROM members WHERE extended_family_id = ?", (session["family_id"],)).fetchall()[0][0]
        db.close()

        return render_template("polls.html", polls=poll_dict, member_count=member_count)


@app.route("/get_selections/", methods=["POST", "GET"])
def get_selections():
    selections = {}
    
    # Define the poll id user clicked for selections
    poll_id = request.args.get("poll_id")

    i = 1
    while True:
        db = get_conn()
        cur = db.cursor()

        # Populate selections until catch arror to determine how many selections does the relevant poll have
        try:
            selection = cur.execute("SELECT selection"+str(i)+" FROM polls WHERE id = ?", (poll_id,)).fetchall()[0][0]
            if selection:
                # If that selection order exists get its selection content vote count and total votes for that poll(to calculate percentage)
                selections["selection"+str(i)] = selection
                selections["selection"+str(i)+"_voteCount"] = cur.execute("SELECT COUNT(*) FROM votes WHERE poll_id = ? AND selection_id = ?", (poll_id, "selection"+str(i)+"")).fetchall()[0][0]
                selections["selection"+str(i)+"_voteTotal"] = cur.execute("SELECT COUNT(*) FROM votes WHERE poll_id = ?", (poll_id,)).fetchall()[0][0]
            i += 1
        except:
            break
    
    db.close()
    
    return jsonify(selections) 
    

@app.route("/start_poll", methods=["POST", "GET"])
def start_poll():
    if request.method == "POST":
        selections = []
        # Populate selections list with the size needed according to number of selections added to new poll
        for i in range(24):
            slct = "selection-" + str(i)
            if request.form.get(slct):
                selections.append(request.form.get(slct))

        # Handle requirements
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

        # Add new pole to polls table in database
        db = get_conn()
        cur = db.cursor()
        cur.execute("INSERT INTO polls (extended_family_id, question, max_selection, expires_on, creator) VALUES(?, ?, ?, ?, ?)", (session["family_id"], request.form.get("question"),
                    request.form.get("max_selection"), request.form.get("last_date"), session["user_id"]))
                    
        # Get crator name and last name for the new poll to post an automatic update to posts page 
        creator = cur.execute("SELECT name, last_name FROM members WHERE id = ?", (session["user_id"],)).fetchall()
        poll_id = cur.lastrowid
        cur.execute("INSERT INTO posts (extended_family_id, author, content, timestamp) VALUES(?, 1, ?, julianday('now'))", (session["family_id"], ""+str(creator[0]["name"])+" "+str(creator[0]["last_name"])+" has started a new poll. Last Date to vote is: "+request.form.get("last_date")+""))

        db.commit()
        
        # Create a selection name field list with the size of selections in new poll 
        columns = []
        columns_id = []
        for i in range(len(selections)):
            columns.append("selection"+str(i+1))
            columns_id.append("selection"+str(i+1)+"_id")

        # Iterate through selections and place each in databse as updating newly created polls selection columns by order.
        for i in range(len(selections)):
            cur.execute("UPDATE polls SET "+columns[i]+" = ?, "+columns_id[i]+" = ? WHERE id = ?", (selections[i], i+1, poll_id))
            db.commit()
        db.close()
        return redirect("/polls")            
    else:
        form = {} 
        return render_template("start-poll.html", form=form)



@app.route("/leave_family", methods=["POST", "GET"])
def leave_family():
    db = get_conn()
    cur = db.cursor()
    # Update database set user family_id column as nulll
    cur.execute("UPDATE members SET extended_family_id = ? WHERE id = ?", (None, session["user_id"]))
    db.commit()
    # Get name and last name of the user left the family to post an automatic update in posts page.
    left_user = cur.execute("SELECT name, last_name FROM members WHERE id = ?", (session["user_id"],)).fetchall()
    cur.execute("INSERT INTO posts (extended_family_id, author, content, timestamp) VALUES(?, 1, ?, julianday('now'))", (session["family_id"], ""+str(left_user[0]["name"])+" "+str(left_user[0]["last_name"])+" has left the family."))

    db.commit()
    db.close()

    # Clear family id in from session data, user will no longer see family page.
    session["family_id"] = ""
    return redirect("/")
        
         

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        db = get_conn()
        cur = db.cursor()
        errors = {}
        # Check requirements
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
            # Send 5 digit token and define it to variable 
            token = send_email()
            print(token)
            # Define token into session variable and redirect to verify_email page to get user input for token 
            session["token"] = token
            db.close()
            return render_template("verify_email.html")            
    
        else:    
            db.close()
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
        db = get_conn()
        cur = db.cursor()
        errors = {}
        # Check requirements
        if not request.form.get("password"):
            errors["login"] = "Please enter your password to login"
        if not request.form.get("email") and not request.form.get("login-name"):
            errors["login"] = "Please submit email or username to login"
        if not errors:
            # If user entered username to login
            if request.form.get("login-name"):
                try:
                    login_name = (request.form.get("login-name")).rstrip()
                    user = (cur.execute("SELECT * FROM members WHERE login_name = ?", (login_name,)).fetchall())[0]
                except:
                    errors["login"] = "Username Not Found"
                    db.close()
                    return render_template("login.html", errors=errors, form=request.form)
                if check_password_hash(user["password_hash"], request.form.get("password")):
                    session["user_id"] = user["id"]
                    session["username"] = user["login_name"]
                    session["family_id"] = user["extended_family_id"]
                    db.close()
                    return redirect("/")
                else:
                    errors["login"] = "Username/Email or Password is Incorrect"
                    db.close()
                    return render_template("login.html", errors=errors, form=request.form)

            # If user entered email to login
            if request.form.get("email"):
                try:
                    user = (cur.execute("SELECT * FROM members WHERE email = ?", [request.form.get("email")]).fetchall())[0]
                except:
                    errors["login"] = "Email Not Found"
                    db.close()
                    return render_template("login.html", errors=errors, form=request.form)

                if check_password_hash(user["password_hash"], request.form.get("password")):
                    session["user_id"] = user["id"]
                    session["username"] = user["login_name"]
                    session["family_id"] = user["extended_family_id"]
                    db.close()
                    return redirect("/")
                else:
                    errors["login"] = "Username/Email or Password is Incorrect"
                    db.close()
                    return render_template("login.html", errors=errors, form=request.form)
                
        else:
            db.close()
            return render_template("login.html", errors=errors, form=request.form)
    else:
        errors = {}
        form = {}
        return render_template("login.html", errors=errors, form=form)    

    
@app.route("/send_email", methods=["GET", "POST"])
def send_email():
        # Generate 5 digit token
        token = random.randint(9999, 99999)
        # Send the token via email

        # !! EMAIL VERIFICATION SYSTEM IS DISABLED FOR DEMO PURPOSES BUT IT IS FUNCTIONAL. CAN CHECK THE TERMINAL FOR TOKEN NOW.
        # msg = EmailMessage()
        # msg["Subject"] = "Confirm your email to get registered at COMMUNE !"
        # msg["From"] = "email here"
        # form = session["form"]
        # msg["To"] = form["email"]
        # mail_out = render_template("mailout.html", token=token)
    
        # msg.add_alternative(mail_out, subtype="html")
        
        # server = smtplib.SMTP("smtp.office365.com", 587)
        # server.starttls()
        # server.login("", "")
        
        # server.send_message(msg)
        
        print("email sent")

        return token

@app.route("/complete-registration", methods=["GET", "POST"])
def verify_email():
    if request.method == "POST":

    
        if int(request.form.get("verification-code")) == session["token"]:
            # Token matches with user input
            db = get_conn()
            cur = db.cursor()
            print("reg success")
            # Register user
            form = session["form"]
            login_name = (form["login-name"]).rstrip()
            cur.execute("INSERT INTO members (name, last_name, birth_date, login_name, email, password_hash, living, registration_date) VALUES (?, ?, ?, ?, ?, ?, 'TRUE', julianday('now'))",
                        (form['name'], form['last-name'], form['birth-date'], login_name, form['email'], generate_password_hash(form['password'])))
            session["user_id"] = cur.execute("SELECT id FROM members WHERE login_name = ?", [login_name]).fetchall()[0][0]
            session["username"] = cur.execute("SELECT login_name FROM members WHERE id = ?", (session["user_id"],)).fetchall()[0][0]
            db.commit()
            db.close()
            # Log user in
            session["form"] = ""           
            return redirect("/")

        else:
            print("reg fail")
            errors = {}
            # Redirect to registration form with error message
            errors["email_verification_fail"] = "Incorrect Verification Code"
            return render_template("register.html", form=session["form"], errors=errors)

        
@app.route("/create-family", methods=["GET", "POST"])
def create_family():
    db = get_conn()
    cur = db.cursor()
    countries = cur.execute("SELECT country FROM countries ORDER BY country").fetchall()
    if request.method == "POST":
        errors = {}
        # Check requirements
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
            errors["password"] = "Password is required"
        if not errors:
            # Add family to databse set user created as admin
            cur.execute("INSERT INTO extended_families (name, login_name, password_hash, origin_country, origin_city, registration_date, admin1) VALUES (?, ?, ?, ?, ?, julianday('now'), ?)",
                        (request.form.get("family-name"), request.form.get("family-login-name"), generate_password_hash(request.form.get("password")), request.form.get("country"), request.form.get("city"),
                        session["user_id"]))
                             
            cur.execute("UPDATE members SET extended_family_id = ? WHERE id = ?", (cur.execute("SELECT id FROM extended_families WHERE admin1 = ?", (session["user_id"],)).fetchall()[0][0], session["user_id"]))
            session["family_id"] = cur.execute("SELECT extended_family_id FROM members WHERE id = ?", (session["user_id"],)).fetchall()[0][0]

            db.commit()
            db.close()
            return redirect("/")
        else:
            db.close()
            return render_template("create_family.html", errors=errors, form=request.form, countries=countries)
    else:
        db.close()
        errors = {}
        form = {}
        return render_template("create_family.html", errors = errors, form = form, countries=countries)
    
@app.route("/join_family", methods=["GET", "POST"])
def join_family():
    if request.method == "POST":
        db = get_conn()
        cur = db.cursor()
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
                db.close()
                return render_template("join_family.html", form=form, errors=errors)
            if not family:
                errors["login"] = "Family is not found"
            # Check family password
            if not check_password_hash(family["password_hash"], request.form.get("password")):
                errors["login"] = "Incorrect Password"
            if not errors:
                # Update user's family id in db
                cur.execute("UPDATE members SET extended_family_id = ? WHERE id = ?", (str(family["id"]), session["user_id"]))
                db.commit()
                session["family_id"] = family["id"]
                # Get name and last name of the requester to post an automatic update in posts
                new_comer = cur.execute("SELECT name, last_name FROM members WHERE id = ?", (session["user_id"],)).fetchall()
                cur.execute("INSERT INTO posts (extended_family_id, author, content, timestamp) VALUES(?, 1, ?, julianday('now'))", (session["family_id"], ""+str(new_comer[0]["name"])+" "+str(new_comer[0]["last_name"])+" has joined the family."))
                db.commit()
                db.close()
                return redirect(url_for('index'))
            else:
                db.close()
                return render_template("join_family.html", form=form, errors=errors)    
        else:
            db.close()
            return render_template("join_family.html", form=form, errors=errors)    
        
        
    else:
        form= {}
        errors= {}
        return render_template("join_family.html", form=form, errors=errors)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    # Get profile data for user profile
    db = get_conn()
    cur = db.cursor()
    profile_data = cur.execute("SELECT *, datetime(registration_date) FROM members WHERE id = ?", (session["user_id"],)).fetchall()
    db.close()
    return render_template("profile.html", profile_data=profile_data)


@app.route("/upload_photo", methods=["GET", "POST"])
def upload_photo():
    if request.method == "POST" and request.args.get('photo') == "upload":
        file = request.files["photo"]
        if not file:
            flash("No file chosen !")
            return redirect("profile")            
        elif not allowed_file(file.filename):
            # Check file extension 
            flash("Only JPG and JPEG files are allowed !")
            return redirect("profile")            

        filename = str((session["user_id"])) + ".jpg"
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        return redirect(url_for('profile'))
    else:
        if request.args.get('photo') == "delete":
            # Delete photo
            filename = str((session["user_id"])) + ".jpg"
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            return redirect("profile")
        else:
            return redirect("profile")

@app.route("/profile/update/", methods=["GET", "POST"])
def update_profile_info():
    db = get_conn()
    cur = db.cursor()
    if request.method == "POST" and request.args.get('update') == "address":
        # Update address
        cur.execute("UPDATE members SET address = ? WHERE id = ?", [request.form.get("address-text"), session["user_id"]])
        db.commit()
        db.close()
        return redirect("/profile")
    elif request.args.get('update') == "delete-address":
        # Delete address
        cur.execute("UPDATE members SET address = ? WHERE id = ?",  (None, session["user_id"]))
        db.commit()
        db.close()
        return redirect("/profile")
    elif request.method == "POST" and request.args.get('update') == "phone_number":
        # Update phone number
        cur.execute("UPDATE members SET phone_number = ? WHERE id = ?", [request.form.get("phone_number"), session["user_id"]])
        db.commit()
        db.close()
        return redirect("/profile")
    elif request.args.get('update') == "delete-phone_number":
        # Delete phone_number
        cur.execute("UPDATE members SET phone_number = ? WHERE id = ?",  (None, session["user_id"]))
        db.commit()
        db.close()
        return redirect("/profile")  

@app.route("/get-city/")
def get_city():
    # Get the cities of the country selected
    db = get_conn()
    cur = db.cursor()
    country = request.args.get('country')
    country_id = cur.execute("SELECT id from countries WHERE country = ?", [country]).fetchall()[0][0]
    city = cur.execute("SELECT city FROM cities WHERE country_id = ?", [country_id]).fetchall()
    cities = [dict(row) for row in city]
    db.close()
    return jsonify(cities)

if __name__ == "__main__":
    app.run(port=8000, debug=True, threaded=True)