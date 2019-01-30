from flask import Flask, render_template, jsonify, request
from EzTrackIt import EzTrackIt, get_packages_for_recipient, get_recipient
from printer.slip import print_slip_from_html
from config import auth

from pathlib import Path
from datetime import datetime
from dateutil import tz

import pickle
import time

app = Flask(__name__)


def parse_mag(data):
    res = ''
    for s in data:
        if s.isdigit():
            res += s
    return res


def load_token(name='TOKEN'):
    if Path(name).is_file():
        try:
            token = pickle.load(open(name, 'rb'))
            if time.time() > (token.get('expires_at', 0) - 3600):
                print('Token Expired!')
                return None
            return token
        except EOFError:
            return None


def eztrackit_login(token_name='TOKEN'):
    client = EzTrackIt(client_id=auth['client_id'], token=load_token(name=token_name))
    if client.login(username=auth['username'], password=auth['password']):
        with open(token_name, 'wb') as tf:
            pickle.dump(client.token(), tf, protocol=pickle.HIGHEST_PROTOCOL)
            print('token saved')
    return client


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/api/recipient/checked-in')
def api_checked_in():
    client = eztrackit_login()
    search = parse_mag(request.args.get('search', '')[:9])

    count = len(get_packages_for_recipient(client=client, student_number=search))
    return jsonify(count=count)


@app.route('/api/print/pick-slip')
def api_print_slip():
    client = eztrackit_login()
    search = parse_mag(request.args.get('search', '')[:9])

    if request.args.get('letter') == 'true':
        letter = True
    else:
        letter = False

    recipient = get_recipient(client=client, search=search)
    if recipient:
        recipient = recipient[0]

        packages = get_packages_for_recipient(client=client, student_number=search)
        if packages or letter:
            count = len(packages)
            now = datetime.now(tz=tz.tzlocal()).strftime('%Y-%m-%d %I:%M %p')
            for pkg in packages:
                if pkg.get('checked_in', None):
                    checked_in = datetime.strptime(pkg['checked_in'], '%Y-%m-%d %H:%M:%S')
                    checked_in = checked_in.replace(tzinfo=tz.tzutc()).astimezone(tz=tz.tzlocal())
                    pkg['checked_in'] = checked_in.strftime('%Y-%m-%d %I:%M %p')

            html = render_template('pick_slip.html', packages=packages, recipient=recipient, letter=letter, now=now)
            print_slip_from_html(html=html)
            return jsonify(status='submitted', count=count, letter=letter)
    return jsonify(status='none', count=0)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
