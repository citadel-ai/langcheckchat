import os
import pickle
import sqlite3
import subprocess
from datetime import datetime

import langcheck
import pytz
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from llama_index import (GPTVectorStoreIndex, ServiceContext,
                         SimpleWebPageReader, StringIterableReader,
                         download_loader, set_global_service_context)
from llama_index.embeddings import OpenAIEmbedding
from llama_index.llms import AzureOpenAI

load_dotenv()

# initalize factual consistency
print(langcheck.metrics.factual_consistency("I'm Bob", "I'm Bob"))
print(langcheck.metrics.ja.factual_consistency("僕はボブ", "僕はボブ"))

SAVED_DOCUMENTS = 'docs.pkl'
if os.path.exists(SAVED_DOCUMENTS):
    with open(SAVED_DOCUMENTS, 'rb') as f:
        documents = pickle.load(f)
else:
    loader = SimpleWebPageReader(html_to_text=True)
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
        "https://langcheck.readthedocs.io/en/latest/langcheck.metrics.en.reference_free_text_quality.html",
        "https://langcheck.readthedocs.io/en/latest/quickstart.html",
    ]
    documents = loader.load_data(urls=pages)

    MarkdownReader = download_loader("MarkdownReader")
    markdown_loader = MarkdownReader()
    markdown_strs = []
    for document in documents:
        markdown_docs = markdown_loader.load_data(file=None,
                                                  content=document.text)
        markdown_strs.append('\n'.join([mdoc.text for mdoc in markdown_docs]))

    documents = StringIterableReader().load_data(markdown_strs)
    with open(SAVED_DOCUMENTS, 'wb') as f:
        pickle.dump(documents, f)

llm = AzureOpenAI(
    model=os.environ['AZURE_OPENAI_API_MODEL'],
    engine=os.environ['AZURE_OPENAI_API_DEPLOYMENT'],
    api_key=os.environ['AZURE_OPENAI_API_KEY'],
    api_base=os.environ['AZURE_OPENAI_API_BASE'],
    api_type='azure',
    api_version='2023-05-15',
)

embed_model = OpenAIEmbedding(
    model=os.environ['AZURE_OPENAI_API_EMBEDDING_MODEL'],
    deployment_name=os.environ['AZURE_OPENAI_API_EMBEDDING_DEPLOYMENT'],
    api_key=os.environ['AZURE_OPENAI_API_KEY'],
    api_base=os.environ['AZURE_OPENAI_API_BASE'],
    api_type='azure',
    api_version='2023-05-15',
)

service_context = ServiceContext.from_defaults(
    llm=llm,
    embed_model=embed_model,
)

set_global_service_context(service_context)

index = GPTVectorStoreIndex.from_documents(documents)


def connect_db():
    return sqlite3.connect(DATABASE)


DATABASE = 'db/langcheckchat.db'


def initialize_db():
    with open('db/chat_log_schema.sql', 'r') as file:
        sql_script = file.read()

    with connect_db() as con:
        cursor = con.cursor()
        cursor.executescript(sql_script)
        con.commit()


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
    language = request.get_json().get('language', 'en')

    # Generate response message
    if language == 'ja':
        user_message_sent = '日本語で答えてください\n' + user_message
    else:
        user_message_sent = user_message
    response = index.as_query_engine().query(user_message_sent)
    response_message = str(response)
    sources = [node.node.text for node in response.source_nodes]
    source = '\n'.join(sources)

    # TODO: Get from user inputs
    language = request.get_json().get('language', 'en')
    print(language)

    if language == 'ja':
        # TODO: Remove this once the problem is fixed in langcheck package
        if len(source) < 512:
            factual_consistency_score = langcheck.metrics.ja.factual_consistency(
                response_message, source).metric_values[0]
        else:
            factual_consistency_score_fst = langcheck.metrics.ja.factual_consistency(
                response_message, source[:len(source) // 2]).metric_values[0]
            factual_consistency_score_snd = langcheck.metrics.ja.factual_consistency(
                response_message, source[len(source) // 2:]).metric_values[0]
            factual_consistency_score = max(factual_consistency_score_fst,
                                            factual_consistency_score_snd)
    else:
        factual_consistency_score = langcheck.metrics.factual_consistency(
            response_message, source).metric_values[0]

    timestamp = datetime.now(
        pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')

    with connect_db() as con:
        cursor = con.cursor()
        cursor.execute(
            'INSERT INTO chat_log (request, response, source, language, factual_consistency, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
            (user_message, response_message, source, language,
             factual_consistency_score, timestamp))
        log_id = cursor.lastrowid
        con.commit()

    subprocess.Popen(["python", "calculate_metrics.py", str(log_id)])
    warning = factual_consistency_score < 0.5

    return jsonify(response=response_message,
                   score=factual_consistency_score,
                   warning=warning,
                   source=source,
                   id=log_id)


@app.route('/api/logs', methods=['GET'])
def logs():
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    con = connect_db()
    cur = con.cursor()
    cur.execute(
        'SELECT request, response, timestamp FROM chat_log ORDER BY timestamp DESC LIMIT ? OFFSET ?',
        (per_page, offset))

    logs = [{
        "request": row[0],
        "response": row[1],
        "timestamp": row[2]
    } for row in cur.fetchall()]
    con.close()

    return jsonify(logs=logs)


@app.route('/api/metrics/<log_id>', methods=['GET'])
def metrics_endpoint(log_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        # Fetch all column names
        cursor.execute('PRAGMA table_info(chat_log)')
        columns = [
            col[1] for col in cursor.fetchall() if col[1] not in
            ["id", "timestamp", "request", "response", "source", "completed"]
        ]

        # Fetch the latest metrics
        cursor.execute(
            "SELECT {} FROM chat_log WHERE id = ?".format(", ".join(columns)),
            (log_id, ))
        data = cursor.fetchone()

        if data is None:
            return jsonify({"error": "No logs available"}), 400

        metrics_data = dict(zip(columns, data))

        cursor.execute("SELECT completed FROM chat_log WHERE id = ?",
                       (log_id, ))
        completed = cursor.fetchone()[0]

        metrics_data["completed"] = completed
        return jsonify(metrics_data)


if __name__ == '__main__':
    initialize_db()
    app.run(host='127.0.0.1', debug=True)
