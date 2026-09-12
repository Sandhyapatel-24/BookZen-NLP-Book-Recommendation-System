from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import sqlite3
import joblib
from sklearn.metrics.pairwise import cosine_similarity
import random
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "bookzen_secret_key"

# -----------------------------
# LOAD DATASET AND ML MODEL
# -----------------------------
df = pd.read_csv("bookzen_books_1200_realistic.csv")

genre_model = joblib.load("bookzen_genre_model.pkl")
tfidf_vectorizer = joblib.load("bookzen_tfidf_vectorizer.pkl")


# -----------------------------
# DATABASE
# -----------------------------
def get_db_connection():
    connection = sqlite3.connect("bookzen.db")
    connection.row_factory = sqlite3.Row
    return connection


# -----------------------------
# GENRE LABEL FIX
# -----------------------------
genre_names = {
    0: "Adventure",
    1: "Biography",
    2: "Fantasy",
    3: "Historical Fiction",
    4: "Historical Romance",
    5: "Horror",
    6: "Mystery",
    7: "Romance",
    8: "Science Fiction",
    9: "Self-Help",
    10: "Thriller",
    11: "Young Adult"
}


# -----------------------------
# PREPROCESSING
# -----------------------------
import re
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# ============================================================
# BOOKZEN DATABASE
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DB_NAME = str(BASE_DIR / "bookzen.db")


stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def remove_stopwords(text):
    tokens = word_tokenize(text)
    return " ".join(
        word for word in tokens
        if word not in stop_words
    )


def lemmatize_text(text):
    tokens = word_tokenize(text)
    return " ".join(
        lemmatizer.lemmatize(word)
        for word in tokens
    )


# -----------------------------
# LOGIN REQUIRED
# -----------------------------
def login_required():
    return "user_id" in session


# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# REGISTER
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        try:
            connection.execute(
                """
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
                """,
                (
                    name,
                    email,
                    generate_password_hash(password)
                )
            )

            connection.commit()
            flash("Registration successful! Please login.")

        except sqlite3.IntegrityError:
            flash("Email already registered.")

        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# -----------------------------
# LOGIN
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# -----------------------------
# DASHBOARD
# -----------------------------


@app.route("/dashboard")
def dashboard():

    if not login_required():
        return redirect(url_for("login"))

    total_books = len(df)

    total_genres = df["genre"].nunique()

    average_rating = round(
        df["rating"].astype(float).mean(),
        2
    )

    # Publication year information
    min_year = int(df["year"].min())
    max_year = int(df["year"].max())

    # User statistics
    favorite_count = 0
    recommendation_count = 0
    most_recommended_genre = "No recommendations yet"
    recent_books = []

    try:

        connection = get_db_connection()

        favorite_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM favorites
            WHERE user_id = ?
            """,
            (session["user_id"],)
        ).fetchone()[0]

        recommendation_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM recommendation_history
            WHERE user_id = ?
            """,
            (session["user_id"],)
        ).fetchone()[0]

        history_rows = connection.execute(
            """
            SELECT book_id, created_at
            FROM recommendation_history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 10
            """,
            (session["user_id"],)
        ).fetchall()

        connection.close()

        # Find most recommended genre
        genres_found = []

        for row in history_rows:

            matching_book = df[
                df["book_id"] == row["book_id"]
            ]

            if not matching_book.empty:
                genres_found.append(
                    matching_book.iloc[0]["genre"]
                )

        if genres_found:

            from collections import Counter

            genre_counts = Counter(genres_found)

            most_recommended_genre = genre_counts.most_common(1)[0][0]

        # Recent recommendation books
        for row in history_rows:

            matching_book = df[
                df["book_id"] == row["book_id"]
            ]

            if not matching_book.empty:

                book_data = matching_book.iloc[0].to_dict()

                book_data["created_at"] = row["created_at"]

                recent_books.append(book_data)

    except Exception as e:

        print("Dashboard history error:", e)

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        total_books=total_books,
        total_genres=total_genres,
        average_rating=average_rating,
        min_year=min_year,
        max_year=max_year,
        favorite_count=favorite_count,
        recommendation_count=recommendation_count,
        most_recommended_genre=most_recommended_genre,
        recent_books=recent_books
    )

@app.route("/search")
def search():

    if not login_required():
        return redirect(url_for("login"))

    query = request.args.get("query", "").strip()
    genre = request.args.get("genre", "").strip()
    min_rating = request.args.get("min_rating", "").strip()
    year = request.args.get("year", "").strip()

    results = df.copy()

    # Search by title, author or description
    if query:
        search_text = (
            results["title"].fillna("").astype(str) + " " +
            results["author"].fillna("").astype(str) + " " +
            results["description"].fillna("").astype(str)
        )

        results = results[
            search_text.str.contains(
                query,
                case=False,
                na=False,
                regex=False
            )
        ]

    # Genre filter
    if genre:
        results = results[
            results["genre"].astype(str) == genre
        ]

    # Rating filter
    if min_rating:
        try:
            results = results[
                results["rating"].astype(float) >= float(min_rating)
            ]
        except:
            pass

    # Publication year filter
    if year:
        try:
            results = results[
                results["year"].astype(int) == int(year)
            ]
        except:
            pass

    results = results.head(50)

    # Check user's favorites
    favorite_ids = set()

    try:
        connection = get_db_connection()

        favorite_rows = connection.execute(
            """
            SELECT book_id
            FROM favorites
            WHERE user_id = ?
            """,
            (session["user_id"],)
        ).fetchall()

        connection.close()

        favorite_ids = {
            row["book_id"]
            for row in favorite_rows
        }

    except:
        favorite_ids = set()

    result_list = []

    for _, book in results.iterrows():

        book_data = book.to_dict()

        book_data["is_favorite"] = (
            book_data["book_id"] in favorite_ids
        )

        result_list.append(book_data)

    genres = sorted(
        df["genre"].dropna().unique().tolist()
    )

    years = sorted(
        df["year"].dropna().astype(int).unique().tolist(),
        reverse=True
    )

    return render_template(
        "search.html",
        results=result_list,
        genres=genres,
        years=years,
        query=query,
        selected_genre=genre,
        min_rating=min_rating,
        selected_year=year
    )

@app.route("/book/<int:book_id>")
def book_details(book_id):

    if not login_required():
        return redirect(url_for("login"))

    book = df[df["book_id"] == book_id]

    if book.empty:
        return "Book not found", 404

    return render_template(
        "book_details.html",
        book=book.iloc[0].to_dict()
    )


# -----------------------------
# RECOMMENDATIONS
# -----------------------------


# ============================================================
# COMPATIBILITY ROUTE
# Supports old /recommend?title=BOOK_TITLE links
# ============================================================

@app.route("/recommend")
def recommend_old():

    if not login_required():
        return redirect(url_for("login"))

    old_title = request.args.get("title", "").strip()

    if not old_title:
        return redirect(url_for("search"))

    matches = df[
        df["title"].astype(str).str.lower() == old_title.lower()
    ]

    # If exact title is not found, try partial title matching
    if matches.empty:

        matches = df[
            df["title"].astype(str).str.contains(
                old_title,
                case=False,
                na=False,
                regex=False
            )
        ]

    if matches.empty:
        flash("Book not found.")
        return redirect(url_for("search"))

    book_id = int(matches.iloc[0]["book_id"])

    return redirect(
        url_for(
            "recommend",
            book_id=book_id
        )
    )


@app.route("/recommend/<int:book_id>")
def recommend(book_id):

    if not login_required():
        return redirect(url_for("login"))

    book_index_list = df.index[
        df["book_id"] == book_id
    ].tolist()

    if not book_index_list:
        return "Book not found", 404

    book_index = book_index_list[0]

    tfidf_matrix = tfidf_vectorizer.transform(
        df["processed_text"]
    ) if "processed_text" in df.columns else tfidf_vectorizer.transform(
        df["description"].apply(clean_text).apply(remove_stopwords).apply(lemmatize_text)
    )

    selected_genre = df.iloc[book_index]["genre"]

    similarity_scores = cosine_similarity(
        tfidf_matrix[book_index],
        tfidf_matrix
    )[0]

    scores = []

    for i, similarity in enumerate(similarity_scores):

        if i == book_index:
            continue

        genre_bonus = 0.20 if df.iloc[i]["genre"] == selected_genre else 0

        final_score = similarity + genre_bonus

        scores.append(
            (
                i,
                similarity,
                final_score
            )
        )

    scores.sort(
        key=lambda x: x[2],
        reverse=True
    )

    top_scores = scores[:5]

    recommendations = []

    for index, similarity, final_score in top_scores:

        book_data = df.iloc[index].to_dict()

        book_data["similarity"] = round(
            similarity * 100,
            2
        )

        recommendations.append(book_data)

    # Save history
    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO recommendation_history
        (user_id, book_id)
        VALUES (?, ?)
        """,
        (
            session["user_id"],
            book_id
        )
    )

    connection.commit()
    connection.close()

    return render_template(
        "recommend.html",
        selected_book=df.iloc[book_index].to_dict(),
        recommendations=recommendations
    )


# -----------------------------
# GENRE PREDICTION
# -----------------------------
@app.route("/predict-genre", methods=["GET", "POST"])
def predict_genre():

    if not login_required():
        return redirect(url_for("login"))

    prediction = None

    if request.method == "POST":

        description = request.form["description"]

        cleaned = clean_text(description)
        no_stopwords = remove_stopwords(cleaned)
        processed = lemmatize_text(no_stopwords)

        text_vector = tfidf_vectorizer.transform(
            [processed]
        )

        predicted_value = genre_model.predict(
            text_vector
        )[0]

        # Convert numeric prediction to genre name
        try:
            prediction = genre_names[int(predicted_value)]
        except (ValueError, TypeError, KeyError):
            prediction = str(predicted_value)

    return render_template(
        "predict_genre.html",
        prediction=prediction
    )


# -----------------------------
# FAVORITES
# -----------------------------
@app.route("/add_favorite/<int:book_id>")
def add_favorite(book_id):

    if not login_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    connection.execute(
        """
        INSERT OR IGNORE INTO favorites
        (user_id, book_id)
        VALUES (?, ?)
        """,
        (
            session["user_id"],
            book_id
        )
    )

    connection.commit()
    connection.close()

    return redirect(request.referrer or url_for("dashboard"))


@app.route("/remove_favorite/<int:book_id>")
def remove_favorite(book_id):

    if not login_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    connection.execute(
        """
        DELETE FROM favorites
        WHERE user_id = ? AND book_id = ?
        """,
        (
            session["user_id"],
            book_id
        )
    )

    connection.commit()
    connection.close()

    return redirect(request.referrer or url_for("favorites"))


@app.route("/favorites")
def favorites():

    if not login_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    favorite_rows = connection.execute(
        """
        SELECT book_id
        FROM favorites
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    favorite_ids = [
        row["book_id"]
        for row in favorite_rows
    ]

    books = df[
        df["book_id"].isin(favorite_ids)
    ].to_dict("records")

    return render_template(
        "favorites.html",
        books=books
    )


# -----------------------------
# SURPRISE ME
# -----------------------------
@app.route("/surprise")
def surprise():

    if not login_required():
        return redirect(url_for("login"))

    book_id = random.choice(
        df["book_id"].tolist()
    )

    return redirect(
        url_for(
            "book_details",
            book_id=book_id
        )
    )


# -----------------------------
# PROFILE
# -----------------------------
@app.route("/profile")
def profile():

    if not login_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    user = connection.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    connection.close()

    return render_template(
        "profile.html",
        user=user
    )


# -----------------------------
# HISTORY
# -----------------------------

@app.route("/history")
def history():

    if not login_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    history_rows = connection.execute(
        """
        SELECT id, book_id, created_at
        FROM recommendation_history
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    history = []

    for row in history_rows:

        matching_book = df[
            df["book_id"] == row["book_id"]
        ]

        if not matching_book.empty:

            book_data = matching_book.iloc[0].to_dict()

            book_data["history_id"] = row["id"]
            book_data["created_at"] = row["created_at"]

            history.append(book_data)

    return render_template(
        "history.html",
        history=history
    )

@app.route("/history/delete/<int:history_id>")
def delete_history(history_id):

    if not login_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    connection.execute(
        """
        DELETE FROM recommendation_history
        WHERE id = ? AND user_id = ?
        """,
        (
            history_id,
            session["user_id"]
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("history"))


@app.route("/history/clear")
def clear_history():

    if not login_required():
        return redirect(url_for("login"))

    connection = get_db_connection()

    connection.execute(
        """
        DELETE FROM recommendation_history
        WHERE user_id = ?
        """,
        (session["user_id"],)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("history"))


# -----------------------------
# START APP
# -----------------------------


# ================= ADMIN ACCOUNT SETUP =================


# ============================================================
# ADMIN ACCOUNT SETUP
# ============================================================

def ensure_admin_account():

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cur.execute(
        "SELECT id FROM admins WHERE email = ?",
        ("admin@bookzen.com",)
    )

    if cur.fetchone() is None:

        cur.execute(
            """
            INSERT INTO admins
            (name, email, password)
            VALUES (?, ?, ?)
            """,
            (
                "BookZen Admin",
                "admin@bookzen.com",
                "admin123"
            )
        )

    conn.commit()
    conn.close()


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    error = None

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row

        admin = conn.execute(
            """
            SELECT *
            FROM admins
            WHERE LOWER(email) = ?
            AND password = ?
            """,
            (email, password)
        ).fetchone()

        conn.close()

        if admin:

            session["admin_logged_in"] = True
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["name"]

            return redirect(url_for("admin_dashboard"))

        error = "Invalid admin email or password."

    return render_template(
        "admin_login.html",
        error=error
    )


# ================= ADMIN LOGOUT =================
@app.route("/admin/logout")
def admin_logout():

    session.pop("admin_logged_in", None)
    session.pop("admin_id", None)
    session.pop("admin_name", None)

    return redirect(url_for("admin_login"))


# ================= ADMIN DASHBOARD =================
@app.route("/admin/dashboard")
def admin_dashboard():

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    total_books = conn.execute(
        "SELECT COUNT(*) AS c FROM books"
    ).fetchone()["c"]

    try:
        total_genres = conn.execute(
            "SELECT COUNT(DISTINCT genre) AS c FROM books"
        ).fetchone()["c"]
    except:
        total_genres = 0

    try:
        avg_rating = conn.execute(
            "SELECT AVG(rating) AS a FROM books"
        ).fetchone()["a"] or 0
    except:
        avg_rating = 0

    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_books=total_books,
        total_genres=total_genres,
        average_rating=round(float(avg_rating), 2),
        admin_name=session.get(
            "admin_name",
            "BookZen Admin"
        )
    )

# ============================================================
# START BOOKZEN APPLICATION
# ============================================================

if __name__ == "__main__":
    ensure_admin_account()
    app.run(
        debug=False,
        use_reloader=False
    )
