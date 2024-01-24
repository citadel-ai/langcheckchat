import os
import subprocess
from datetime import datetime

import langcheck
import pytz
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request

import database as db
from calculate_metrics import add_init_to_db, get_factual_consistency
from rag import RAG

api_routes_blueprint = Blueprint('api', __name__)
load_dotenv()

# initalize factual consistency
if os.environ['ENABLE_LOCAL_LANGCHECK_MODELS'] == 'True':
    print('Computing factual consistency..')
    print(langcheck.metrics.factual_consistency("I'm Bob", "I'm Bob"))
    print(langcheck.metrics.ja.factual_consistency("僕はボブ", "僕はボブ"))

# Initialize the RAG system
rag_system = RAG()


@api_routes_blueprint.route('/api/chat', methods=['POST'])
@api_routes_blueprint.route('/api/chat_demo', methods=['POST'])
def chat():
    user_message = request.get_json().get('message', '')
    language = request.get_json().get('language', 'en')

    if request.path == '/api/chat_demo':
        # Get canned responses to speed up live demos
        response_message, source = rag_system.query_demo(
            user_message, language)
    else:
        response_message, source = rag_system.query(user_message, language)

    # Compute the factual consistency score and add it along with the chat
    # data to the db
    factual_consistency_score, factual_consistency_explanation = get_factual_consistency(
        response_message, source, language)

    timestamp = datetime.now(
        pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')

    log_id = add_init_to_db(user_message, response_message, source, language,
                            factual_consistency_score,
                            factual_consistency_explanation, timestamp)

    # Compute and log all the other metrics
    subprocess.Popen(["python", "calculate_metrics.py", str(log_id)])
    warning = factual_consistency_score < 0.5

    return jsonify(response=response_message,
                   score=factual_consistency_score,
                   warning=warning,
                   source=source,
                   id=log_id)


@api_routes_blueprint.route('/api/ref_metric', methods=['POST'])
def get_reference_based_metric():
    log_id = request.get_json().get('log_id', '')
    reference_text = request.get_json().get('reference')

    # Update the status before updating the record
    db.update_chatlog_by_id({'status': 'new'}, log_id)

    # Compute the metrics
    subprocess.Popen([
        "python", "calculate_reference_metrics.py",
        str(log_id), reference_text
    ])
    return jsonify(success=True)


@api_routes_blueprint.route('/api/logs', methods=['GET'])
def logs():
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page
    return jsonify(logs=db.get_chatlogs_and_metrics(per_page, offset))


@api_routes_blueprint.route('/api/logs_comparison', methods=['GET'])
def logs_comparison():
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page
    return jsonify(
        logs=db.get_comparison_chatlogs_and_metrics(per_page, offset))


@api_routes_blueprint.route('/api/metrics/<log_id>', methods=['GET'])
def metrics_endpoint(log_id):
    metrics_data = db.get_metrics_by_log_id(log_id)
    if metrics_data is None:
        return jsonify({"error": "No metrics available"}), 400
    chatlog_data = db.get_chatlog_by_id(log_id)
    if chatlog_data is None:
        return jsonify({"error": "No chat logs available"}), 400
    metrics_data['status'] = chatlog_data['status']
    return jsonify(metrics_data)
