from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from dotenv import load_dotenv
from database import (
    init_db, create_user, get_user_by_email, get_user_by_id,
    save_quiz, save_flashcards, get_user_quizzes, get_user_flashcards,
    get_quiz_by_id, get_flashcard_by_id, update_quiz_score
)
from extractor import extract_text
from ai_generator import generate_quiz, generate_flashcards

load_dotenv()

app = Flask(__name__)
app.secret_key = "quizforge_secret_key_2024"

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "docx", "pptx"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

init_db()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# -------- LANDING PAGE --------

@app.route("/")
def index():
    return render_template("index.html")

# -------- AUTH ROUTES --------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name").strip()
        email = request.form.get("email").strip().lower()
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if not name or not email or not password:
            return render_template("register.html", error="All fields are required.")
        if password != confirm:
            return render_template("register.html", error="Passwords do not match.")
        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters.")

        hashed = generate_password_hash(password)
        success = create_user(name, email, hashed)

        if not success:
            return render_template("register.html", error="Email already registered. Please login.")

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email").strip().lower()
        password = request.form.get("password")

        user = get_user_by_email(email)

        if not user or not check_password_hash(user["password"], password):
            return render_template("login.html", error="Invalid email or password.")

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# -------- DASHBOARD --------

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    quizzes = get_user_quizzes(user_id)
    flashcards = get_user_flashcards(user_id)
    return render_template("dashboard.html",
                           user_name=session["user_name"],
                           quizzes=quizzes,
                           flashcards=flashcards)

# -------- CHOOSE MODE --------

@app.route("/choose")
@login_required
def choose():
    return render_template("choose.html")

# -------- UPLOAD --------

@app.route("/upload/<mode>")
@login_required
def upload(mode):
    return render_template("upload.html", mode=mode)

@app.route("/process", methods=["POST"])
@login_required
def process():
    mode = request.form.get("mode")
    file = request.files.get("file")

    if not file or file.filename == "":
        return render_template("upload.html", mode=mode, error="Please select a file.")

    if not allowed_file(file.filename):
        return render_template("upload.html", mode=mode, error="File type not supported.")

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    text = extract_text(file_path)

    if not text or len(text.strip()) < 100:
        return render_template("upload.html", mode=mode, error="Could not extract enough text from the file. Please try another file.")

    title = os.path.splitext(filename)[0]
    user_id = session["user_id"]

    if mode == "quiz":
        questions = generate_quiz(text)
        quiz_id = save_quiz(user_id, title, questions)
        os.remove(file_path)
        return redirect(url_for("quiz", quiz_id=quiz_id))

    elif mode == "flash":
        cards = generate_flashcards(text)
        fc_id = save_flashcards(user_id, title, cards)
        os.remove(file_path)
        return redirect(url_for("flashcard", fc_id=fc_id))

    return redirect(url_for("dashboard"))

# -------- QUIZ --------

@app.route("/quiz/<int:quiz_id>")
@login_required
def quiz(quiz_id):
    quiz_data = get_quiz_by_id(quiz_id)
    if not quiz_data:
        return redirect(url_for("dashboard"))
    questions = json.loads(quiz_data["questions"])
    return render_template("quiz.html",
                           quiz_id=quiz_id,
                           title=quiz_data["title"],
                           questions=questions)

@app.route("/save_score", methods=["POST"])
@login_required
def save_score():
    data = request.get_json()
    quiz_id = data.get("quiz_id")
    score = data.get("score")
    update_quiz_score(quiz_id, score)
    return jsonify({"status": "ok"})

# -------- FLASHCARD --------

@app.route("/flashcard/<int:fc_id>")
@login_required
def flashcard(fc_id):
    fc_data = get_flashcard_by_id(fc_id)
    if not fc_data:
        return redirect(url_for("dashboard"))
    cards = json.loads(fc_data["cards"])
    return render_template("flashcard.html",
                           fc_id=fc_id,
                           title=fc_data["title"],
                           cards=cards)

# -------- HISTORY --------

@app.route("/history")
@login_required
def history():
    user_id = session["user_id"]
    quizzes = get_user_quizzes(user_id)
    flashcards = get_user_flashcards(user_id)

    quizzes_parsed = []
    for q in quizzes:
        quizzes_parsed.append({
            "id": q["id"],
            "title": q["title"],
            "score": q["score"],
            "created_at": q["created_at"],
            "count": len(json.loads(q["questions"]))
        })

    flashcards_parsed = []
    for f in flashcards:
        flashcards_parsed.append({
            "id": f["id"],
            "title": f["title"],
            "created_at": f["created_at"],
            "count": len(json.loads(f["cards"]))
        })

    return render_template("history.html",
                           quizzes=quizzes_parsed,
                           flashcards=flashcards_parsed)

if __name__ == "__main__":
    app.run(debug=True)