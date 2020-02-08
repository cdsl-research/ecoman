from flask import Flask, render_template, escape

import connect


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # JSONでの日本語文字化け対策
# app.jinja_env.filters['resolve_esxi_addr'] = lambda host: connect.app_resolve_esxi_addr(host)


@app.route('/', methods=['GET'])
def top():
    return render_template('top.html', title='TOP', machines=connect.app_top())


@app.route('/machine/<string:uniq_id>', methods=['GET'])
def detail(uniq_id):
    my_title = escape('DETAIL: '+uniq_id)
    return render_template('detail.html', title=my_title, detail=connect.app_detail(uniq_id), navigation=(
        {'href':'#', 'caption':'Power OFF'},
        {'href':'#', 'caption':'Power ON'},
        {'href':'#', 'caption':'Suspend'},
    ))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
