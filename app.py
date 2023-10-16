from flask import Flask, request, jsonify
from datetime import datetime
import sqlite3
import pickle
import os

from dotenv import load_dotenv

load_dotenv()
from llama_index import GPTVectorStoreIndex, download_loader

SAVED_DOCUMENTS = 'docs.pkl'
if os.path.exists(SAVED_DOCUMENTS):
    with open(SAVED_DOCUMENTS, 'rb') as f:
        documents = pickle.load(f)
else:
    SimpleWebPageReader = download_loader("SimpleWebPageReader")

    loader = SimpleWebPageReader()
    pages = [
        "https://langcheck.readthedocs.io/en/latest/langcheck.html",
        "https://langcheck.readthedocs.io/en/latest/langcheck.metrics.en.reference_based_text_quality.html",
        "https://langcheck.readthedocs.io/en/latest/installation.html",
        "https://langcheck.readthedocs.io/en/latest/metrics.html",
        "https://langcheck.readthedocs.io/en/latest/langcheck.utils.io.html",
        "https://langcheck.readthedocs.io/en/latest/index.html",
        "https://langcheck.readthedocs.io/en/latest/langcheck.metrics.ja.reference_free_text_quality.html",
        "https://langcheck.readthedocs.io/en/latest/langcheck.metrics.html",
        "https://langcheck.readthedocs.io/en/latest/langcheck.metrics.ja.html",
        "https://langcheck.readthedocs.io/en/latest/py-modindex.html",
        "https://langcheck.readthedocs.io/en/latest/langcheck.metrics.metric_value.html",
        "https://langcheck.readthedocs.io/en/latest/langcheck.metrics.text_structure.html",
        "https://langcheck.readthedocs.io/en/latest/langcheck.plot.html",
        "https://langcheck.readthedocs.io/en/latest/genindex.html",
        "https://langcheck.readthedocs.io/en/latest/langcheck.metrics.en.source_based_text_quality.html",
        "https://langcheck.readthedocs.io/en/latest/contributing.html",
        "https://langcheck.readthedocs.io/en/latest/langcheck.metrics.en.html",
        "https://langcheck.readthedocs.io/en/latest/langcheck.metrics.reference_based_text_quality.html",
        "https://langcheck.readthedocs.io/en/latest/langcheck.metrics.ja.reference_based_text_quality.html",
        "https://langcheck.readthedocs.io/en/latest/langcheck.utils.html",
        "https://langcheck.readthedocs.io/en/latest/https://www.sbert.net/docs/usage/semantic_textual_similarity.html",
        "https://langcheck.readthedocs.io/en/latest/langcheck.metrics.en.reference_free_text_quality.html",
        "https://langcheck.readthedocs.io/en/latest/quickstart.html",
    ]
    documents = loader.load_data(urls=pages)
    with open(SAVED_DOCUMENTS, 'wb') as f:
        pickle.dump(documents, f)

index = GPTVectorStoreIndex.from_documents(documents)


def connect_db():
    return sqlite3.connect(DATABASE)


DATABASE = 'db/langcheckchat.db'

app = Flask(__name__)


@app.route('/', methods=['GET'])
def home():
    return app.send_static_file('index.html')


@app.route('/logs', methods=['GET'])
def log_page():
    return app.send_static_file('logs.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.get_json().get('message', '')
    # Generate response message
    response_message = str(index.as_query_engine().query(user_message))
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    con = connect_db()
    con.execute(
        'INSERT INTO chat_log (request, response, timestamp) VALUES (?, ?, ?)',
        (user_message, response_message, timestamp))
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
        (per_page, offset))

    logs = [{
        "request": row[0],
        "response": row[1],
        "timestamp": row[2]
    } for row in cur.fetchall()]
    con.close()

    return jsonify(logs=logs)


if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)
