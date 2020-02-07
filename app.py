from flask import Flask, request, jsonify, render_template
import os
import json
import connect


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # JSONでの日本語文字化け対策


@app.route('/', methods=['GET'])
def index():
    return render_template('top.tpl', machines=connect.app_top())


@app.route('/power/<string:my_vmid>/<string:state>', methods=['GET'])
def power(my_vmid, state):
    return ''.join(connect.set_vm_power(state, my_vmid))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
