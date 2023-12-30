from flask import Flask

import database as db
from api_routes import api_routes_blueprint

app = Flask(__name__)
app.register_blueprint(api_routes_blueprint)


@app.route('/', methods=['GET'])
@app.route('/demo', methods=['GET'])
def home():
    return app.send_static_file('index.html')


@app.route('/logs', methods=['GET'])
def log_page():
    return app.send_static_file('logs.html')


if __name__ == '__main__':
    db.initialize_db()
    app.run(host='127.0.0.1', debug=True)
