import os
import hmac
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

load_dotenv()

# Create Flask app
app = Flask(__name__)

# -----------------------------
# Security settings
# -----------------------------
# On Vercel these MUST be set as Environment Variables (the app refuses to
# start without them, so a public default can never be used in production).
# On your own computer a harmless local default is used instead.
IS_VERCEL = bool(os.environ.get("VERCEL"))


def require_env(name, local_default):
    value = os.environ.get(name)
    if value:
        return value
    if IS_VERCEL:
        raise RuntimeError(f"{name} environment variable must be set on Vercel.")
    return local_default


app.secret_key = require_env("SECRET_KEY", "local-dev-only-secret-key")
ADMIN_USERNAME = require_env("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = require_env("ADMIN_PASSWORD", "1234")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"      # blocks cross-site form posts
app.config["SESSION_COOKIE_SECURE"] = IS_VERCEL    # HTTPS-only cookie in production

# -----------------------------
# Database configuration
# -----------------------------
# If a DATABASE_URL environment variable is set (e.g. your Supabase Postgres
# connection string), use that. Otherwise fall back to the local SQLite file
# so nothing breaks when running on your own machine without any setup.
database_url = os.environ.get("DATABASE_URL", "sqlite:///database.db")

# Supabase/Heroku-style URLs start with "postgres://" but SQLAlchemy needs
# "postgresql://" — this line fixes that automatically.
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db = SQLAlchemy(app)

# -----------------------------
# Login guards
# -----------------------------

def safe_equal(a, b):
    """Constant-time string comparison."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def admin_required(view):
    """Only a logged-in administrator may open this page."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin"))
        return view(*args, **kwargs)
    return wrapper


def student_required(view):
    """Only a logged-in student may open this page."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("student_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


@app.after_request
def no_cache(response):
    # Stops the browser Back button from showing protected pages after logout
    if request.endpoint != "static":
        response.headers["Cache-Control"] = "no-store"
    return response

# -----------------------------
# Database Tables
# -----------------------------

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_class = db.Column(db.String(20), nullable=False)
    has_voted = db.Column(db.Boolean, default=False)

# -----------------------------
# Routes
# -----------------------------

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():

    if session.get("is_admin"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if safe_equal(username, ADMIN_USERNAME) and safe_equal(password, ADMIN_PASSWORD):
            session.clear()
            session["is_admin"] = True
            return redirect(url_for("dashboard"))

        else:
            return "Invalid Username or Password", 401

    return render_template("admin_login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/dashboard")
@admin_required
def dashboard():

    student_count = Student.query.count()

    candidate_count = Candidate.query.count()

    position_count = Position.query.count()

    voted_count = Student.query.filter_by(has_voted=True).count()

    return render_template(
        "dashboard.html",
        student_count=student_count,
        candidate_count=candidate_count,
        position_count=position_count,
        voted_count=voted_count
    )


@app.route("/students", methods=["GET", "POST"])
@admin_required
def students():

    if request.method == "POST":

        print("Form Submitted!")

        name = request.form["name"]
        student_class = request.form["student_class"]

        print(name, student_class)

        new_student = Student(
            name=name,
            student_class=student_class
        )

        db.session.add(new_student)
        db.session.commit()

        print("Student Saved!")

        return redirect(url_for("students"))

    all_students = Student.query.all()

    return render_template(
        "students.html",
        students=all_students
    )

# -----------------------------
# Election Tables
# -----------------------------

class Position(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    candidates = db.relationship(
        "Candidate",
        backref="position",
        lazy=True,
        cascade="all, delete"
    )


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    position_id = db.Column(
        db.Integer,
        db.ForeignKey("position.id"),
        nullable=False
    )

    votes = db.Column(db.Integer, default=0)


@app.route("/candidates", methods=["GET", "POST"])
@admin_required
def candidates():

    if request.method == "POST":

        name = request.form["name"]
        position_id = request.form["position"]

        candidate = Candidate(
            name=name,
            position_id=position_id
        )

        db.session.add(candidate)
        db.session.commit()

        return redirect(url_for("candidates"))

    positions = Position.query.all()
    candidates = Candidate.query.all()

    return render_template(
        "candidates.html",
        positions=positions,
        candidates=candidates

    )



@app.route("/positions", methods=["GET", "POST"])
@admin_required
def positions():

    if request.method == "POST":

        position_name = request.form["position_name"]

        position = Position(name=position_name)

        db.session.add(position)
        db.session.commit()

        return redirect(url_for("positions"))

    all_positions = Position.query.all()

    return render_template(
        "positions.html",
        positions=all_positions
    )

@app.route("/delete_position/<int:id>", methods=["POST"])
@admin_required
def delete_position(id):

    position = Position.query.get_or_404(id)

    db.session.delete(position)
    db.session.commit()

    return redirect(url_for("positions"))

@app.route("/delete_candidate/<int:id>", methods=["POST"])
@admin_required
def delete_candidate(id):

    candidate = Candidate.query.get_or_404(id)

    db.session.delete(candidate)
    db.session.commit()

    return redirect(url_for("candidates"))


@app.route("/delete_student/<int:id>", methods=["POST"])
@admin_required
def delete_student(id):

    student = Student.query.get_or_404(id)

    db.session.delete(student)
    db.session.commit()

    return redirect(url_for("students"))

@app.route("/upload_students", methods=["POST"])
@admin_required
def upload_students():

    file = request.files["excel_file"]

    data = pd.read_excel(file)

    for index, row in data.iterrows():

        existing_student = Student.query.filter_by(
            name=row["Name"],
            student_class=row["Class"]
        ).first()

        if existing_student:
            continue

        student = Student(
            name=row["Name"],
            student_class=row["Class"]
        )

        db.session.add(student)

    db.session.commit()

    return redirect(url_for("students"))

@app.route("/setup")
@admin_required
def setup():
    return render_template("setup.html")

@app.route("/sample")
@admin_required
def sample():

    if Position.query.count() == 0:

        head_boy = Position(name="Head Boy")
        head_girl = Position(name="Head Girl")
        sports = Position(name="Sports Captain")

        db.session.add_all([
            head_boy,
            head_girl,
            sports
        ])

        db.session.commit()

    return "Positions Added!"

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        name = request.form["name"]
        student_class = request.form["student_class"]

        student = Student.query.filter_by(
            name=name,
            student_class=student_class
        ).first()

        if student:

            if student.has_voted:
                return "You have already voted."

            session.clear()
            session["student_id"] = student.id
            return redirect(url_for("vote"))

        else:
            return "Student not found."

    return render_template("login.html")


@app.route("/vote", methods=["GET", "POST"])
@student_required
def vote():

    student = Student.query.get(session["student_id"])

    # Student was deleted, or already voted -> end the session
    if student is None:
        session.clear()
        return redirect(url_for("login"))

    if student.has_voted:
        session.clear()
        return "You have already voted."

    if request.method == "POST":

        # 1. Check every choice is a real candidate for that position
        chosen = []

        for position_id, candidate_id in request.form.items():

            try:
                position_id = int(position_id)
                candidate_id = int(candidate_id)
            except ValueError:
                return "Invalid ballot.", 400

            candidate = Candidate.query.get(candidate_id)

            if candidate is None or candidate.position_id != position_id:
                return "Invalid ballot.", 400

            chosen.append(candidate_id)

        if not chosen:
            return "Invalid ballot.", 400

        # 2. Claim the vote first. This only succeeds once per student,
        #    even if the form is submitted twice at the same moment.
        claimed = Student.query.filter_by(
            id=student.id,
            has_voted=False
        ).update({"has_voted": True}, synchronize_session=False)

        if claimed != 1:
            db.session.rollback()
            session.clear()
            return "You have already voted."

        # 3. Count the votes
        for candidate_id in chosen:
            Candidate.query.filter_by(id=candidate_id).update(
                {"votes": Candidate.votes + 1},
                synchronize_session=False
            )

        db.session.commit()

        # Voting is finished, so log the student out
        session.clear()

        return redirect(url_for("success"))

    positions = Position.query.all()

    return render_template(
        "vote.html",
        positions=positions
    )


@app.route("/results")
@admin_required
def results():

    positions = Position.query.all()

    total_votes = 0
    leaders = {}

    for position in positions:

        highest_votes = -1
        leader = None

        for candidate in position.candidates:

            total_votes += candidate.votes

            if candidate.votes > highest_votes:
                highest_votes = candidate.votes
                leader = candidate

        leaders[position.id] = leader

    return render_template(
        "results.html",
        positions=positions,
        total_votes=total_votes,
        leaders=leaders
    )

@app.route("/reset_election", methods=["POST"])
@admin_required
def reset_election():

    # Reset all candidates' votes
    candidates = Candidate.query.all()

    for candidate in candidates:
        candidate.votes = 0

    # Allow all students to vote again
    students = Student.query.all()

    for student in students:
        student.has_voted = False

    db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/success")
def success():
    return render_template("success.html")


# -----------------------------
# Run the App
# -----------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
