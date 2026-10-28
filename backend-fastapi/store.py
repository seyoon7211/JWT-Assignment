import os, sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timezone
from users import find_public

_file = Path(os.getenv("DB_FILE", "data/board.sqlite"))
_file.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def connect():
    db = sqlite3.connect(_file)
    db.row_factory = sqlite3.Row
    try:
        with db:
            yield db
    finally:
        db.close()


with connect() as db:
    db.execute(
        "CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,content TEXT NOT NULL,author_id INTEGER NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL)"
    )


def shape(row):
    if row is None:
        return None
    return dict(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        authorId=row["author_id"],
        authorName=find_public(row["author_id"])["name"],
        createdAt=row["created_at"],
        updatedAt=row["updated_at"],
    )


def list_posts():
    with connect() as db:
        return [shape(r) for r in db.execute("SELECT * FROM posts ORDER BY id DESC")]


def get_post(post_id):
    with connect() as db:
        return shape(
            db.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
        )


def create_post(data, user_id):
    now = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        post_id = db.execute(
            "INSERT INTO posts(title,content,author_id,created_at,updated_at) VALUES(?,?,?,?,?)",
            (data["title"], data["content"], user_id, now, now),
        ).lastrowid
    return get_post(post_id)


def update_post(post_id, data):
    with connect() as db:
        db.execute(
            "UPDATE posts SET title=?,content=?,updated_at=? WHERE id=?",
            (
                data["title"],
                data["content"],
                datetime.now(timezone.utc).isoformat(),
                post_id,
            ),
        )
    return get_post(post_id)


def delete_post(post_id):
    with connect() as db:
        db.execute("DELETE FROM posts WHERE id=?", (post_id,))
