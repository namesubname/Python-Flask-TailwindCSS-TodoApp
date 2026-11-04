from logging import log
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, redirect, render_template, request, flash, url_for
from flask_login import LoginManager, \
    UserMixin, \
    login_required, \
    login_user, \
    logout_user, \
    current_user
from contextlib import closing
from database import get_connection
from datetime import date as dt


app = Flask(__name__)
# app["SECRET_KEY"]

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

login_manager.login_message = None


class User(UserMixin):
    def __init__(self, id) -> None:
        self.id = id


@login_manager.user_loader
def load_user(id):
    return User(id)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = str(request.form.get("username"))
        password = str(request.form.get("password"))
        remember_me = True if request.form.get("remember_me") else False

        with closing(get_connection()) as conn:
            with conn:
                user = conn.execute(
                    "SELECT * FROM users \
                     WHERE username = ?", (username,)).fetchone()

        if user is None or not check_password_hash(user["password"], password):
            flash("Неверный логин или пароль!", "error")
            return render_template("login.html", username=username)

        login_user(User(id=username), remember=remember_me)
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = str(request.form.get("username"))
        password = str(request.form.get("password"))
        confirm_password = str(request.form.get("confirm_password"))

        if password != confirm_password:
            flash("Пароли не совпадают!", "error")
            return render_template("register.html", username=username)

        elif not username.isalnum():
            flash("Разрешены только буквы и цифры в логине!", "error")
            return render_template("register.html", username=username)

        hashed_password = generate_password_hash(password, method='pbkdf2')

        try:
            with closing(get_connection()) as conn:
                with conn:
                    conn.execute(
                        "INSERT INTO users (username, password) \
                         VALUES (?, ?)", (username, hashed_password))
        except sqlite3.IntegrityError:
            flash("Имя пользователя занято!", "error")
            return render_template("register.html")

        login_user(User(id=username))
        return redirect("/")

    else:

        return render_template("register.html")


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта.", "success")
    return redirect(url_for("login"))


@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    username = current_user.id

    with closing(get_connection()) as conn:
        with conn:
            notes = conn.execute(
                "SELECT * FROM notes WHERE username = ?", (username,)).fetchall()

    active = [n for n in notes if not n["completed"]]
    completed = [n for n in notes if n["completed"]]

    return render_template(template_name_or_list="home.html",
                           active=active,
                           completed=completed,
                           user_initials=username[0].upper(),
                           username=username)


@app.route("/add-todo", methods=["POST", "GET"])
@login_required
def add_todo():
    if request.method == "POST":
        username = current_user.id
        title = str(request.form.get("title"))
        date = dt.today().isoformat()

        with closing(get_connection()) as conn:
            with conn:
                conn.execute("INSERT INTO notes \
                    (username, title, completed, date) \
                    VALUES (?, ?, ?, ?)",
                             (username, title, 0, date))

        return redirect(url_for("home"))

    else:
        return redirect(url_for("home"))


@app.route("/toggle/<int:note_id>", methods=["GET"])
@login_required
def toggle(note_id):
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        with conn:
            note = conn.execute(
                "SELECT * FROM notes WHERE id = ? and username = ?", (note_id, current_user.id)).fetchone()

            if note:
                if current_user.id == note["username"]:
                    status = 1 if note["completed"] == 0 else 0

                    conn.execute(
                        """UPDATE notes SET completed = ?
                         WHERE id = ?""", (status, note_id))

    return redirect(url_for("home"))


@app.route("/delete/<int:note_id>", methods=["GET"])
@login_required
def delete(note_id):
    with closing(get_connection()) as conn:
        conn.row_factory = sqlite3.Row
        with conn:
            note = conn.execute(
                "DELETE FROM notes WHERE id = ? AND username = ?", (note_id, current_user.id)).fetchone()

            if note:
                status = 1 if note["completed"] == 0 else 0

                conn.execute(
                    """UPDATE notes SET completed = ?
                         WHERE id = ?""", (status, note_id))

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
