from curses import endwin
import json
from optparse import Values
import string
from urllib.request import HTTPDigestAuthHandler
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from redis import DataError
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from wtforms.fields import DateField, TimeField, HiddenField
from passlib.hash import sha256_crypt
from functools import wraps
import redis


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please log in to see this page.", category="danger")
            return redirect(url_for("login"))

    return decorated_function


class RegisterForm(Form):
    username = StringField(
        "Username:",
        validators=[
            validators.Length(min=4, message="Username must be at least 4 characters."),
            validators.DataRequired(message="This field cannot be empty."),
        ],
    )
    email = StringField(
        "Email:",
        validators=[
            validators.Email(message="Please enter a valid email address."),
            validators.DataRequired(message="This field cannot be empty."),
        ],
    )
    password = PasswordField(
        "Password:",
        validators=[
            validators.DataRequired(message="This field cannot be empty."),
            validators.EqualTo(fieldname="confirm", message="Passwords do not match."),
        ],
    )
    confirm = PasswordField(
        "Confirm Password:", validators=[validators.DataRequired(message="This field cannot be empty.")]
    )


class EventForm(Form):
    id = HiddenField("")

    event = StringField(
        "Title:",
        validators=[
            validators.DataRequired(message="This field cannot be empty."),
        ],
    )
    startDate = DateField(
        "Starting Date:",
        validators=[
            validators.DataRequired(message="This field cannot be empty."),
        ],
    )
    endDate = DateField(
        "Ending Date:",
        validators=[
            validators.DataRequired(message="This field cannot be empty."),
        ],
    )
    startTime = TimeField(
        "Starting Time:",
        validators=[
            validators.DataRequired(message="This field cannot be empty."),
        ],
        format="%H:%M",
    )
    endTime = TimeField(
        "ending Time:",
        validators=[
            validators.DataRequired(message="This field cannot be empty."),
        ],
        format="%H:%M",
    )


app = Flask(__name__)
app.secret_key = "calendarapp"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "calendarapp"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

redis = redis.Redis(host="redis", port="6379", decode_responses=True)

userIdCntr = redis.get("userIdCntr")
if userIdCntr == None:
    redis.set("userIdCntr", "1")
    userIdCntr = int(redis.get("userIdCntr"))
userIdCntr = int(userIdCntr)

eventIdCntr = redis.get("eventIdCntr")
if eventIdCntr == None:
    redis.set("eventIdCntr", "1")
    eventIdCntr = int(redis.get("eventIdCntr"))
eventIdCntr = int(eventIdCntr)


@app.route("/", methods=["POST", "GET"])
def index():
    global eventIdCntr
    form = EventForm(request.form)
    if request.method == "POST":
        title = form.event.data
        start = str(form.startDate.data) + "T" + str(form.startTime.data)
        end = str(form.endDate.data) + "T" + str(form.endTime.data)
        eventId = form.id.data
        userid = session["id"]

        result = redis.hgetall(f"eventuserid:{str(userid)}")
        if result and eventId:
            data = [str(i) for i in result.values()]
            try:
                for i in data:
                    if str(i) == str(eventId):
                        map = {"title": title, "start": start, "end": end}
                        redis.hset(f"event:{str(eventId)}", mapping=map)
                        flash(message="Succesfully modified event", category="success")
                        return redirect(url_for("index"))
                    else:
                        continue
            except (TypeError, ValueError):
                map = {"id": eventIdCntr, "title": title, "start": start, "end": end, "userid": userid}
                redis.hset(f"event:{str(eventIdCntr)}", mapping=map)
                redis.hset(f"eventuserid:{userid}", mapping={f"event{str(eventIdCntr)}": str(eventIdCntr)})
                eventIdCntr += 1
                redis.set("eventIdCntr", eventIdCntr)
                flash(message="Succesfully added event.", category="success")
                return redirect(url_for("index"))
        else:
            map = {"id": eventIdCntr, "title": title, "start": start, "end": end, "userid": userid}
            redis.hset(f"event:{str(eventIdCntr)}", mapping=map)
            redis.hset(f"eventuserid:{userid}", mapping={f"event{str(eventIdCntr)}": str(eventIdCntr)})
            eventIdCntr += 1
            redis.set("eventIdCntr", eventIdCntr)
            flash(message="Succesfully added event.", category="success")
            return redirect(url_for("index"))

    else:
        return render_template("index.html", form=form)


@app.route("/list")
@login_required
def list():

    data = redis.hgetall(f"eventuserid:{session['id']}")
    eventids = [i for i in data.values()]
    will_send = "["
    for i in eventids:
        result = redis.hgetall(f"event:{i}")
        jstext = json.dumps(result, indent=4, sort_keys=True, default=str)
        will_send += jstext
        will_send += ","
    will_send = will_send[:-1]
    will_send += "]"
    return will_send


@app.route("/tryx")
def tryx():
    return userIdCntr


@app.route("/delete/<string:id>")
@login_required
def deleteEvent(id):

    result = redis.hgetall(f"event:{id}")
    if result:
        redis.delete(f"event:{id}")
        flash("Succesfully deleted event.", category="success")
        return redirect(url_for("index"))
    else:
        flash("Failed to delete event. Either you don't have permission or event does not exist.", category="danger")
        return redirect(url_for("index"))


@app.route("/drop/<string:id>/<string:start>/<string:end>")
@login_required
def dropEvent(id, start, end):
    result = redis.hgetall(f"event:{id}")
    if result:
        map = {"start": start, "end": end}
        redis.hset(f"event:{id}", mapping=map)
        flash(message="Succesfully modified event", category="success")
        return redirect(url_for("index"))
    else:
        flash("Failed to modify event. Either you don't have permission or event does not exist.", category="danger")
        return redirect(url_for("index"))


@app.route("/login", methods=["POST", "GET"])
def login():
    form = RegisterForm(request.form)

    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        userid = redis.get("username:" + username)
        if userid:
            data = redis.hgetall("user:" + userid)
            real_password = data["password"]
            if sha256_crypt.verify(password_entered, real_password):
                flash(message="Successfully logged in.", category="success")

                session["logged_in"] = True
                session["username"] = username
                session["id"] = userid

                return redirect(url_for("index"))
            else:
                flash(message="Username or password is incorrect.", category="danger")
                return redirect(url_for("login"))

        else:
            flash(message="Username or password is incorrect.", category="danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html", form=form)


@app.route("/register", methods=["POST", "GET"])
def register():
    global userIdCntr
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        if redis.get("username:" + username):
            flash(message="This username is taken. Please change your username.", category="danger")
            return redirect(url_for("register"))
        else:

            map = {"username": username, "email": email, "password": password}
            redis.hset("user:" + str(userIdCntr), mapping=map)
            redis.set("username:" + username, str(userIdCntr))
            userIdCntr += 1
            redis.set("userIdCntr", userIdCntr)

            flash(message="Succesfully registered. Please log in.", category="success")
            return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash(message="Succesfully logged out.", category="success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
