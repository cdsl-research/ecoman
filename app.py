from flask import Flask, request, jsonify, render_template
import os
import json
from connect import esxi


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # JSONでの日本語文字化け対策


@app.route('/', methods=['GET'])
def index():
    return render_template('main.tpl', machines=esxi().values())


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
