import sqlite3
import subprocess
from datetime import datetime

import pytz
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from time import sleep

EXAMPLE_Q_A = [
    {
        'question': 'LangCheck社の福利厚生について教えてください。',
        'right': {
            'response': 'LangCheck社の福利厚生には、\n健康保険および厚生年金の加入\n退職金制度\n子育て支援制度(保育補助、育児休暇など)\nスポーツクラブやレジャー施設の割引利用\n社員食堂の提供\n学術・研究会への参加支援\nのような内容が含まれます。',
            'factual_consistency_score': 0.652806
        },
        'wrong': {
            'response': 'LangCheck社の福利厚生には、\nフィナンシャルプランニング支援\nリモートワーク補助\n住宅ローン補助\nのような内容が含まれます。',
            'factual_consistency_score': 0.060735
        },
        'source': 'LangCheck社 福利厚生ポリシー\n\nLangCheck社では、福利厚生として以下のようなサポートを社員に提供しています。\n\n- 健康保険・厚生年金の加入\n- 退職金制度\n- 子育て支援制度\n- 外部施設の割引利用\n- 社員食堂\n- 学術・研究会への参加支援\n\nなお、以下のようなサービスは現在は対象としておりません。今後の対応を予定しております。\n- フィナンシャルプランニング支援\n- リモートワーク補助\n- 住宅ローン補助'
    },
    {
        'question': '顧客からのクレーム対応についてまず初めに対処するべき内容は何ですか。',
        'right': {
            'response': '顧客からクレームを受けた場合、まずクレーム内容、日時、連絡先、関係者などの情報を収集し業務システムに記録してください。',
            'factual_consistency_score': 0.618151
        },
        'wrong': {
            'response': '顧客からクレームを受けた場合、まず顧客への解決策を 12 時間以内に具体的に提案してください。',
            'factual_consistency_score': 0.024938
        },
        'source': 'LangCheck社　クレーム対応マニュアル\n\n顧客からクレームを受けた場合、以下の手順にしたがって対応してください。\n- まず最初に、クレーム内容、日時、連絡先、関係者などの情報を収集し業務システムに記録してください。\n- 次に、対応する部署からのシステム上での返答を待ってください。\n- 返答があり次第、それに従ってお客様に連絡し、必要に応じてフォローアップを行ってください。'
    },
    {
        'question': '新製品 LangCheck Parrot はいつリリース予定ですか。',
        'right': {
            'response': 'LangCheck Parrotの発売予定日は2022年2月15日です。',
            'factual_consistency_score': 0.927797
        },
        'wrong': {
            'response': 'LangCheck Parrotの発売予定日は2022年4月1日です。',
            'factual_consistency_score': 0.003726
        },
        'source': '-- プロダクトロードマップ 2022 --\n2022年上半期に予定された新製品とその発売予定日は以下のようになっています。\nLangCheck Elephant: 2022年1月20日発売予定です。\nLangCheck Parrot: 2022年2月15日発売予定です。\nLangCheck Tiger: 2022年4月1日に発売予定です。'
    },
    {
        'question': 'Salesforce にアクセスができない。どのように対処すれば良いか。',
        'right': {
            'response': 'Salesforce にアクセスできない場合、次の手順を試してください。\n- インターネット接続を確認してください。\n- ブラウザのキャッシュをクリアしてみてください。\n- Salesforceのダウンタイムを確認してください。\n- サポートチームに連絡してください。',
            'factual_consistency_score': 0.652574
        },
        'wrong': {
            'response': 'Salesforce にアクセスできない場合、次の手順を試してください。\n- パスワードのリセットリンクをクリックしてください。\n- パスワードのリセットメールをチェックしてください。\n- パスワードのリセット方法を確認してください。',
            'factual_consistency_score': 0.311967
        },
        'source': 'Salesforce アクセストラブルシューティングガイド\n\nSalesforceにアクセスできない場合は、まずインターネット接続を確認する。Wi-Fiやモバイルデータなどの接続が安定していることを確認する。\n次にブラウザのキャッシュをクリアする。一時的な通信の問題が原因である場合、キャッシュをクリアすることで解決することがある。\n次にSalesforceのダウンタイムを確認する。定期メンテナンスやシステムアップデートによる、一時的なアクセス制限の可能性あり。\n解決しない場合、サポートチームに連絡する。問題が継続する場合、サポートチームに解決策を求めることができる。\n\nSalesforceのパスワードを忘れた場合は、まずパスワードのリセットリンクをクリックする。ログイン画面で「パスワードをお忘れですか?」というリンクがある場合、クリックするとリセット手続きが始まる。\n次にパスワードのリセットメールをチェックする。登録されているメールアドレスにパスワードのリセットリンクが送信されるので、受信したらリンクをクリックして新しいパスワードを設定する。\nパスワードのリセット方法を確認する。企業によっては、セキュリティポリシーやディレクトリ統合などの設定により、パスワードリセットの手順が異なる場合がある。その場合、IT 部門やシステム管理者に相談して適切な手順を確認する　。'
    },
    {
        'question': 'クライアントへの製品の配送期間はどのくらいですか?',
        'right': {
            'response': '通常、クライアントへの製品の配送は注文から 3 営業日以内に完了されています。',
            'factual_consistency_score': 0.726461
        },
        'wrong': {
            'response': '通常、クライアントへの製品の配送は注文の翌日に完了されています。',
            'factual_consistency_score': 0.254557
        },
        'source': '物流部　配送プロセス詳細ドキュメント\n\nまず、発注の翌日以内に製品がクライアントの居住地域に到着します。その後クライアントへの製品の発送が行われます。ここまでが通常3営業日以内に完了されます。'
    },
    {
        'question': 'LangCheck Parrot は顧客からの要望に対応するため、カスタマイズは可能ですか?',
        'right': {
            'response': 'LangCheck Parrot では、顧客の要望に対応するため、いくつか有料のカスタマイズオプションを提供しています。',
            'factual_consistency_score': 0.915266
        },
        'wrong': {
            'response': 'LangCheck Parrot をカスタマイズすることはできません　。',
            'factual_consistency_score': 0.001218
        },
        'source': 'LangCheck Parrot カスタマイズ対応ガイド　\n\nLangCheck Parrotでは、保証期間延長、カラーリング変更等のカスタマイズオプションを有料で提供しています。これによって、より柔軟に顧客の要望に対応することができます。'
    },
]

load_dotenv()


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


@app.route('/api/chat', methods=['POST'])
def chat():
    sleep(3)
    qa_id = int(request.get_json()['id'])
    # TODO: Add a flag for right/wrong
    used_bot = request.get_json()['botType']
    language = 'ja'
    user_message = EXAMPLE_Q_A[qa_id]['question']
    response_message = EXAMPLE_Q_A[qa_id][used_bot]['response']
    factual_consistency_score = EXAMPLE_Q_A[qa_id][used_bot]['factual_consistency_score']
    source = EXAMPLE_Q_A[qa_id]['source']

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

@app.route('/api/questions', methods=['GET'])
def questions():
    return [qa['question'] for qa in EXAMPLE_Q_A]


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
