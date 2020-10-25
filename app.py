import os
from flask import Flask, flash, render_template, redirect, request, session, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_tasks")
def get_tasks():
    tasks = list(mongo.db.tasks.find())
    return render_template("tasks.html", tasks=tasks)


@app.route("/signup", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one({"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("sign_up"))
        # creating a new user
        signup = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")),
            "location": request.form.get("location").upper()
        }
        mongo.db.users.insert_one(signup)

        # put the new user in session cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful")
        return redirect(url_for("agents", username=session["user"]))
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def log_in():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one({"username": request.form.get("username").lower()})

        if existing_user:
            # make sure hashed password matches the user input
            if check_password_hash(existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome back {}!".format(request.form.get("username").capitalize()))
                return redirect(url_for("agents", username=session["user"]))
            else:
                # if invalid password match
                flash("Invalid Username and/or Password")
                return redirect(url_for("log_in"))
        else:
            # if username doesn't exists yet
            flash("Invalid Username and/or Password")
            return redirect(url_for("log_in"))

    return render_template("login.html")


@app.route("/agents/<username>", methods=["GET", "POST"])
def agents(username):
    # grab the session user's username from mongo db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"].capitalize()
    

    if session["user"]:
        return render_template("agents.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def log_out():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("log_in"))


@app.route("/add_booking", methods=["GET", "POST"])
def add_booking():
    if request.method == "POST":
        is_refunded = "on" if request.form.get("is_refunded") else "off"
        task = {
            "task_pnr": request.form.get("task_pnr"),
            "pax_name": request.form.get("pax_name"),
            "task_airline": request.form.get("task_airline"),
            "ticket_number": request.form.get("ticket_number"),
            "date_issue": request.form.get("date_issue"),
            "is_refunded": is_refunded,
            "created_by": session["user"]
        }
        mongo.db.tasks.insert_one(task)
        flash("New Booking Added")
        return redirect(url_for("get_tasks"))
    return render_template("add_booking.html")


@app.route("/update_booking/<task_id>")
def update_booking(task_id):
    task = mongo.db.tasks.find_one({"_id": ObjectId(task_id)})

    return render_template("update_booking.html", task=task)

if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
        port=int(os.environ.get("PORT")),
        debug=True)  
