from flask import Flask, request, jsonify
from datetime import datetime
import sqlite3

DATABASE = 'db/langcheckchat.db'

app = Flask(__name__)


def connect_db():
    return sqlite3.connect(DATABASE)


@app.route('/', methods=['GET'])
def home():
    return app.send_static_file('index.html')


@app.route('/logs', methods=['GET'])
def log_page():
    return app.send_static_file('logs.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.get_json().get('message', '')
    # Generate response message, in a real application, possibly using ML model
    response_message = "Echo: " + user_message
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    con = connect_db()
    con.execute(
        'INSERT INTO chat_log (request, response, timestamp) VALUES (?, ?, ?)',
        (user_message, response_message, timestamp)
    )
    con.commit()
    con.close()

    return jsonify(response=response_message)


@app.route('/api/logs', methods=['GET'])
def logs():
    page = int(request.args.get('page', 1))
    per_page = 5
    offset = (page - 1) * per_page

    con = connect_db()
    cur = con.cursor()
    cur.execute(
        'SELECT request, response, timestamp FROM chat_log LIMIT ? OFFSET ?',
        (per_page, offset)
    )

    logs = [
        {"request": row[0], "response": row[1], "timestamp": row[2]}
        for row in cur.fetchall()
    ]
    con.close()

    return jsonify(logs=logs)


if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)
