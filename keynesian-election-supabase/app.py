import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

load_dotenv()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "school_voting_secret_key")

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

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            return redirect(url_for("dashboard"))

        else:
            return "Invalid Username or Password"

    return render_template("admin_login.html")


@app.route("/dashboard")
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

    # How many candidates a voter may select for this position.
    # 1 = normal single-choice position, 4 = "pick up to 4" position, etc.
    max_selections = db.Column(db.Integer, nullable=False, default=1)

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
def delete_position(id):

    position = Position.query.get_or_404(id)

    db.session.delete(position)
    db.session.commit()

    return redirect(url_for("positions"))

@app.route("/delete_candidate/<int:id>", methods=["POST"])
def delete_candidate(id):

    candidate = Candidate.query.get_or_404(id)

    db.session.delete(candidate)
    db.session.commit()

    return redirect(url_for("candidates"))


@app.route("/delete_student/<int:id>", methods=["POST"])
def delete_student(id):

    student = Student.query.get_or_404(id)

    db.session.delete(student)
    db.session.commit()

    return redirect(url_for("students"))

@app.route("/upload_students", methods=["POST"])
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
def setup():
    return render_template("setup.html")

@app.route("/sample")
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

            session["student_id"] = student.id
            return redirect(url_for("vote"))

        else:
            return "Student not found."

    return render_template("login.html")


@app.route("/vote", methods=["GET", "POST"])
def vote():

    if request.method == "POST":

        selected_candidates = request.form

        for position_id, candidate_id in selected_candidates.items():

            candidate = Candidate.query.get(int(candidate_id))

            if candidate:
                candidate.votes += 1
                student = Student.query.get(session["student_id"])
                student.has_voted = True

        db.session.commit()

        return redirect(url_for("success"))

    positions = Position.query.all()

    return render_template(
        "vote.html",
        positions=positions
    )


@app.route("/results")
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
@app.route("/test")
@app.route("/test")
def test():
    student = Student(
        name="Amber",
        student_class="A2"
    )

    db.session.add(student)
    db.session.commit()

    return "Student Added!"
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
