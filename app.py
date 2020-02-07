from flask import Flask, request, jsonify, render_template, escape
import os
import json
import connect


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # JSONでの日本語文字化け対策


@app.route('/', methods=['GET'])
def index():
    return render_template('top.html', title='TOP', machines=connect.app_top())


@app.route('/power/<string:my_vmid>', methods=['GET'])
def power(my_vmid):
    my_title = escape('POWER :'+my_vmid)
    return render_template('power.html', title=my_title, detail=connect.get_vm_detail(my_vmid), navigation=(
        {'href':'#', 'caption':'Power OFF'},
        {'href':'#', 'caption':'Power ON'},
        {'href':'#', 'caption':'Suspend'},
        ))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
