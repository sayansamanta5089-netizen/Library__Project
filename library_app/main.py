from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import date

app = FastAPI()

templates = Jinja2Templates(directory="templates")


def get_db():
    conn = sqlite3.connect("library.db")
    conn.row_factory = sqlite3.Row
    return conn


# CREATE DATABASE TABLES
conn = get_db()

conn.execute("""
CREATE TABLE IF NOT EXISTS books(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
author TEXT,
year TEXT,
added_date TEXT,
borrow_date TEXT,
return_date TEXT,
available INTEGER
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS reviews(
id INTEGER PRIMARY KEY AUTOINCREMENT,
book_id INTEGER,
content TEXT
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS notifications(
id INTEGER PRIMARY KEY AUTOINCREMENT,
message TEXT
)
""")

conn.commit()
conn.close()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    conn = get_db()

    books = conn.execute("SELECT * FROM books").fetchall()

    notifications = conn.execute(
        "SELECT message FROM notifications ORDER BY id DESC"
    ).fetchall()

    notification_count = len(notifications)

    total_books = conn.execute(
        "SELECT COUNT(*) FROM books WHERE available=1"
    ).fetchone()[0]

    book_data = []

    for book in books:

        reviews = conn.execute(
            "SELECT * FROM reviews WHERE book_id=?",
            (book["id"],)
        ).fetchall()

        book_data.append({
            "id": book["id"],
            "title": book["title"],
            "author": book["author"],
            "year": book["year"],
            "available": book["available"],
            "reviews": reviews
        })

    conn.close()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "books": book_data,
            "notifications": notifications,
            "notification_count": notification_count,
            "total_books": total_books
        }
    )


# ADD BOOK
@app.post("/add_book")
def add_book(title: str = Form(...), author: str = Form(...), year: str = Form(...)):

    conn = get_db()

    conn.execute(
        "INSERT INTO books(title,author,year,added_date,available) VALUES(?,?,?,?,1)",
        (title, author, year, str(date.today()))
    )

    conn.execute(
        "INSERT INTO notifications(message) VALUES(?)",
        (f"📚 Book added: {title}",)
    )

    conn.commit()
    conn.close()

    return RedirectResponse("/", status_code=303)


# BORROW BOOK
@app.post("/borrow")
def borrow(book_id: int = Form(...)):

    conn = get_db()

    book = conn.execute(
        "SELECT title FROM books WHERE id=?",
        (book_id,)
    ).fetchone()

    conn.execute(
        "UPDATE books SET available=0, borrow_date=? WHERE id=?",
        (str(date.today()), book_id)
    )

    conn.execute(
        "INSERT INTO notifications(message) VALUES(?)",
        (f"📕 Book borrowed: {book['title']}",)
    )

    conn.commit()
    conn.close()

    return RedirectResponse("/", status_code=303)


# RETURN BOOK
@app.post("/return")
def return_book(book_id: int = Form(...)):

    conn = get_db()

    book = conn.execute(
        "SELECT title FROM books WHERE id=?",
        (book_id,)
    ).fetchone()

    conn.execute(
        "UPDATE books SET available=1, return_date=? WHERE id=?",
        (str(date.today()), book_id)
    )

    conn.execute(
        "INSERT INTO notifications(message) VALUES(?)",
        (f"📗 Book returned: {book['title']}",)
    )

    conn.commit()
    conn.close()

    return RedirectResponse("/", status_code=303)


# ADD REVIEW
@app.post("/review")
def review(book_id: int = Form(...), content: str = Form(...)):

    conn = get_db()

    conn.execute(
        "INSERT INTO reviews(book_id,content) VALUES(?,?)",
        (book_id, content)
    )

    conn.execute(
        "INSERT INTO notifications(message) VALUES(?)",
        (f"💬 Review added: {content}",)
    )

    conn.commit()
    conn.close()

    return RedirectResponse("/", status_code=303)


# DELETE BOOK
@app.post("/delete")
def delete(book_id: int = Form(...)):

    conn = get_db()

    conn.execute("DELETE FROM books WHERE id=?", (book_id,))

    conn.execute(
        "INSERT INTO notifications(message) VALUES('❌ Book deleted')"
    )

    conn.commit()
    conn.close()

    return RedirectResponse("/", status_code=303)


# CLEAR NOTIFICATIONS
@app.post("/clear_notifications")
def clear_notifications():

    conn = get_db()

    conn.execute("DELETE FROM notifications")

    conn.commit()
    conn.close()

    return RedirectResponse("/", status_code=303)