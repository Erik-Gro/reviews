import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify

# --- НАСТРОЙКА ПРИЛОЖЕНИЯ И БАЗЫ ДАННЫХ ---

app = Flask(__name__)
DATABASE_NAME = "reviews.db"


def get_db_connection():
    """Создает и возвращает соединение с базой данных SQLite."""
    conn = sqlite3.connect(DATABASE_NAME)
    # Позволяет обращаться к колонкам по их именам, а не по индексам
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Инициализирует базу данных: создаёт таблицу, если она не существует."""
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                text        TEXT    NOT NULL,
                sentiment   TEXT    NOT NULL,
                created_at  TEXT    NOT NULL
            );
        """)
        conn.commit()
        conn.close()



# --- БИЗНЕС-ЛОГИКА: АНАЛИЗ ТОНАЛЬНОСТИ ---

def analyze_sentiment(text):
    """
    Определяет тональность текста по простому словарю ключевых слов.
    """
    text_lower = text.lower()
    positive_words = ["хорош", "отличн", "супер", "люблю", "нравится", "прекрасн"]
    negative_words = ["плохо", "ужасн", "ненавиж", "отврат", "не работ"]

    if any(word in text_lower for word in positive_words):
        return "positive"
    elif any(word in text_lower for word in negative_words):
        return "negative"
    else:
        return "neutral"


# --- API ЭНДПОИНТЫ (МАРШРУТЫ) ---

@app.route('/reviews', methods=['POST'])
def create_review():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Missing 'text' in request body"}), 400

    review_text = data['text']
    sentiment = analyze_sentiment(review_text)
    created_at = datetime.utcnow().isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reviews (text, sentiment, created_at) VALUES (?, ?, ?)",
        (review_text, sentiment, created_at)
    )
    conn.commit()

    review_id = cursor.lastrowid
    conn.close()

    response_data = {
        "id": review_id,
        "text": review_text,
        "sentiment": sentiment,
        "created_at": created_at
    }
    return jsonify(response_data), 201  


@app.route('/reviews', methods=['GET'])
def get_reviews_by_sentiment():
    sentiment_filter = request.args.get('sentiment')
    if not sentiment_filter:
        return jsonify({"error": "Query parameter 'sentiment' is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews WHERE sentiment = ?", (sentiment_filter,))
    rows = cursor.fetchall()
    conn.close()

    reviews_list = [dict(row) for row in rows]

    return jsonify(reviews_list), 200  


# --- ЗАПУСК ПРИЛОЖЕНИЯ ---

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
