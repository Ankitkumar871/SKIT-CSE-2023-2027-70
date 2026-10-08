import sqlite3
from datetime import datetime
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "chatbot.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            source TEXT,
            tag TEXT,
            confidence REAL,
            language TEXT,
            feedback INTEGER,
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def save_conversation(
    user_message,
    bot_response,
    source,
    tag,
    confidence,
    language
):
    connection = get_connection()

    cursor = connection.execute("""
        INSERT INTO conversations (
            user_message,
            bot_response,
            source,
            tag,
            confidence,
            language,
            feedback,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_message,
        bot_response,
        source,
        tag,
        confidence,
        language,
        None,
        datetime.now().isoformat(timespec="seconds")
    ))

    conversation_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return conversation_id


def get_conversations(limit=20):
    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM conversations
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def save_feedback(conversation_id, feedback):
    connection = get_connection()

    cursor = connection.execute("""
        UPDATE conversations
        SET feedback = ?
        WHERE id = ?
    """, (feedback, conversation_id))

    connection.commit()
    updated = cursor.rowcount > 0

    connection.close()

    return updated


def get_statistics():
    connection = get_connection()

    total = connection.execute(
        "SELECT COUNT(*) FROM conversations"
    ).fetchone()[0]

    intent_count = connection.execute(
        "SELECT COUNT(*) FROM conversations WHERE source = 'intent'"
    ).fetchone()[0]

    gemini_count = connection.execute(
        "SELECT COUNT(*) FROM conversations WHERE source = 'gemini'"
    ).fetchone()[0]

    positive_feedback = connection.execute(
        "SELECT COUNT(*) FROM conversations WHERE feedback = 1"
    ).fetchone()[0]

    negative_feedback = connection.execute(
        "SELECT COUNT(*) FROM conversations WHERE feedback = 0"
    ).fetchone()[0]

    connection.close()

    return {
        "total_conversations": total,
        "intent_responses": intent_count,
        "gemini_responses": gemini_count,
        "positive_feedback": positive_feedback,
        "negative_feedback": negative_feedback
    }


def clear_conversations():
    connection = get_connection()

    connection.execute("DELETE FROM conversations")

    connection.commit()
    connection.close()
