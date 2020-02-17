from flask import Flask, render_template, escape, request, jsonify
import json

import connect


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # JSONでの日本語文字化け対策
# app.jinja_env.filters['resolve_esxi_addr'] = lambda host: connect.app_resolve_esxi_addr(host)


@app.route('/', methods=['GET'])
def top():
    return render_template('top.html', title='TOP', machines=connect.app_top())


@app.route('/machine/<string:uniq_id>', methods=['GET'])
def detail(uniq_id):
    uniq_id_safe = escape(uniq_id)
    return render_template('detail.html', title='DETAIL: '+uniq_id_safe, uniq_id=uniq_id_safe, detail=connect.app_detail(uniq_id))


@app.route('/create', methods=['GET'])
def create_vm():
    return render_template('create.html', title='CREATE VM')


@app.route('/v1/add', methods=['POST'])
def add_vm():
    """
    curl -s -XPOST -d '{"name":"myvm","cpu":1,"ram":500,"ssd":30,"network":"dmz","os":"ubuntu1804","user":"myadmin","password":"my12pass34word56","hostname":"myvm","tag":"foo,bar","memo":"this is memo"}'  "http://192.168.100.3:3000/v1/add"
    """
    # Parse Request
    req_data = request.get_data()
    req_txt = req_data.decode('utf-8')
    # Get Request body
    payload = json.loads(req_txt)
    vm_spec = {
        "name": payload.get('name'),
        "cpu": payload.get('cpu'),
        "ram": payload.get('ram'),
        "ssd": payload.get('ssd'),
        "network": payload.get('network'),
        "os": payload.get('os'),
        "user": payload.get('user'),
        "password": payload.get('password'),
        "hostname": payload.get('hostname'),
        "tag": payload.get('tag'),
        "memo": payload.get('memo'),
    }
    return jsonify(payload)


@app.route('/v1/power/<string:uniq_id>', methods=['POST'])
def set_power(uniq_id):
    """
    curl -s -XPOST -d '{"state": "on"}'  "http://192.168.100.3:3000/v1/power/jasmine|38"
    """
    # Parse Request
    req_data = request.get_data()
    req_txt = req_data.decode('utf-8')
    payload = json.loads(req_txt)
    # Get Request status
    power_state = payload.get('state')
    # Change status
    result = connect.app_set_power(uniq_id, power_state)
    return jsonify({"status": "ok", "detail": result})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
