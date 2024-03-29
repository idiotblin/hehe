from random import randint, getrandbits, shuffle
from flask import Flask, render_template, abort, redirect, request, url_for, session, _app_ctx_stack
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.orm import scoped_session
from sqlalchemy import desc

import models
from models import User, Conn, Work
from database import SessionLocal, engine

import datetime
import json
import os
import requests
import smtplib

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.secret_key = os.environ['secret'].encode()

app.session = scoped_session(SessionLocal, scopefunc=_app_ctx_stack.__ident_func__)

models.Base.metadata.create_all(bind=engine)


@app.route('/')
def menu():
    s = "<li><a href='/task1/random/'>/task1/random/</a></li>\n" \
        "<li><a href='/task1/i_will_not/'>/task1/i_will_not/</a></li>"
    return f'<ul id=menu>{s}</ul>'


@app.route('/haba/')
def hello_world():
    s = ['Hello, Haba!',
         'Hello, Arsen!',
         'Hello, Karim!']
    out = "<pre>{}</pre>".format("\n".join(s))
    return out


@app.route('/task1/random/')
def task1_random():
    r = randint(1, 5)
    s = "Haba's mark is " + str(r)
    out = "<pre>{}</pre>".format(s)
    return out


@app.route('/task1/i_will_not/')
def task1_i_will_not():
    s = "<li>I will not waste time</li>\n" * 100
    return f'<ul id=blackboard>{s}</ul>'


@app.route('/task2/avito/<city>/<category>/<ad>/')
def task2_avito(city, category, ad):
    s = f'''<h1>debug info</h1>
    <p>city={city} category={category} ad={ad}</p>
    <h1>{ad.replace('_', ' ')}</h1>
    <p>{city} {category} {ad}</p>
    '''
    return s


@app.route('/task2/cf/profile/<username>/')
def task2_cf(username):
    info = json.loads(requests.get(f'https://codeforces.com/api/user.info?handles={username}').text)
    if info['status'] != 'OK':
        return 'User not found'
    else:
        s = f'''<table id=stats border="1">
        <tr>
        <td>User</td>
        <td>Rating</td>
        </tr>
        <tr>
        <td>{username}</td>
        <td>{info["result"][0]["rating"]}</td>
        </tr>
        </table>'''
        return s


def numIntoWords(num):
    a = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    b = ["", "ten", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    c = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
    ans = ""
    if num == 0:
        ans += "zero"
    ans += a[num // 100]
    if num >= 100:
        ans += " hundred "
    num -= num // 100 * 100
    if num >= 20:
        ans += b[num // 10] + " "
        num -= num // 10 * 10
    elif num >= 10:
        ans += c[num - 10] + " "
        num = 0
    ans += a[num] + " "
    return ans.strip()


@app.route('/task2/num2words/<int:num>/')
def task2_num(num):
    if 0 <= num < 1000:
        res = {"status": "OK", "number": num, "isEven": num % 2 == 0, "words": numIntoWords(num)}
    else:
        res = {"status": "FAIL"}
    return f'{json.dumps(res)}'


@app.route('/task3/cf/profile/<handle>/')
def task3_cf_profile_no_page(handle):
    return redirect(f'/task3/cf/profile/{handle}/page/1')


@app.route('/task3/cf/profile/<handle>/page/<int:page_number>/')
def task3_cf_profile(handle, page_number):
    data = json.loads(requests.get(f'https://codeforces.com/api/user.status?handle={handle}&from=1&count=100').text)
    if data['status'] != 'OK':
        abort(404)
    problem = list()
    problem.append(list())
    ind = 0
    for attempt in data['result']:
        problem[ind].append((attempt['creationTimeSeconds'], attempt['problem']['name'], attempt['verdict']))
        if len(problem[ind]) == 25:
            ind += 1
            problem.append(list())
    if not 0 < page_number <= len(problem):
        abort(404)
    if len(problem) == 5:
        problem.pop()
    link = list()
    link.append(('Previous', f'/task3/cf/profile/{handle}/page/{page_number - 1}/'))
    for i in range(len(problem)):
        link.append((i + 1, f'/task3/cf/profile/{handle}/page/{str(i + 1)}/'))
    link.append(('Next', f'/task3/cf/profile/{handle}/page/{page_number + 1}/'))
    return render_template('pagination.html', problem=problem, page=page_number, link=link, page_kol=len(problem))


@app.route('/task3/cf/top/')
def top():
    data = request.args
    url = 'https://codeforces.com/api/user.info?handles={}'
    ans = list()
    try:
        orderby = data['orderby']
    except:
        orderby = "None"
    for i in data['handles'].split('|'):
        handle = str(requests.get(url.format(i)).json()['result'][0]["handle"])
        ans.append([f'/task3/cf/profile/{handle}/', handle, requests.get(url.format(i)).json()['result'][0]['rating']])
    y, reverse = (-2, False) if orderby == "None" else (-1, True)
    ans.sort(key=lambda x: x[y], reverse=reverse)
    return render_template("top.html", ans=ans)


@app.errorhandler(404)
def cf_error_page(error):
    return render_template("404_not_found.html"), 404


data_set = {
    "token": os.environ['token'],
    "secret": os.environ['secret'],
    "command": "set",
    "key": "",
    "value": ""
}

data_get = {
    "token": os.environ['token'],
    "secret": os.environ['secret'],
    "command": "get",
    "key": ""
}


@app.route('/task4/santa/create', methods=['GET', 'POST'])
def create():
    if request.method == 'GET':
        return render_template('create_game.html')
    form = request.form
    name = form['name']
    code = str(getrandbits(64))
    secret = str(getrandbits(64))
    link_player = f'/task4/santa/play/{code}'
    link_creator = f'/task4/santa/toss/{code}/{secret}'
    data_set['key'] = code
    data_set['value'] = json.dumps({"name": name, "code": code, "secret": secret, "play": link_player,
                                    "organize": link_creator, "active": "True", "players": []})
    requests.post("https://arsenwisheshappy2021.herokuapp.com/query", data=data_set)
    return render_template("game_created.html", link_player=link_player, link_creator=link_creator)


@app.route('/task4/santa/play/<link>', methods=["GET", "POST"])
def play(link):
    no_game_error = 'error'
    no_name_error = 'error'
    url = f'/task4/santa/play/{link}'
    data_get["key"] = link
    if request.method == 'GET':
        game = json.loads(requests.post("https://arsenwisheshappy2021.herokuapp.com/query", data=data_get).text)
        no_game = False
        if game["active"] == "False":
            no_game = True
        return render_template('player_registration.html', url=url, no_game=no_game, no_game_error=no_game_error,
                               no_name_error=no_name_error)
    form = request.form
    if form["name"].strip() == '':
        return render_template('player_registration.html', url=url, no_name=True, no_game_error=no_game_error,
                               no_name_error=no_name_error)
    name = form["name"]
    game = json.loads(requests.post("https://arsenwisheshappy2021.herokuapp.com/query", data=data_get).text)
    game["players"].append(name)
    data_set["key"] = link
    data_set["value"] = json.dumps(game)
    requests.post("https://arsenwisheshappy2021.herokuapp.com/query", data=data_set)
    return render_template("player_registered.html", name=name)


@app.route("/task4/santa/toss/<link>/<secret>", methods=["GET", "POST"])
def toss(link, secret):
    no_game_error = 'error'
    no_players_error = 'error'
    url = f'/task4/santa/toss/{link}/{secret}'
    data_get["key"] = link
    game = json.loads(requests.post("https://arsenwisheshappy2021.herokuapp.com/query", data=data_get).text)
    players = game["players"]
    if request.method == "GET":
        no_game = game["active"] == "False"
        no_players = len(players) == 0 or len(players) % 2 == 1
        return render_template("toss_players.html", url=url, no_game=no_game, no_game_error=no_game_error,
                               no_players=no_players, no_players_error=no_players_error, players=players)
    shuffle(players)
    game["active"] = "False"
    data_set["key"] = link
    data_set["value"] = json.dumps(game)
    requests.post("https://arsenwisheshappy2021.herokuapp.com/query", data=data_set)
    return render_template('players_are_tossed.html', players=players, size=len(players))


def is_human(captcha_response):
    if session.get('enable', False):
        return True
    secret = os.environ['secret_key']
    payload = {'response': captcha_response, 'secret': secret}
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", payload)
    response_text = json.loads(response.text)
    return response_text['success']


@app.route('/task5/test/enable')
def enable():
    session['enable'] = True
    return redirect(url_for('sign_up_step_1'))


@app.route('/task5/test/disable')
def disable():
    session['enable'] = False
    return redirect(url_for('sign_up_step_1'))


@app.route('/task5/sign-up', methods=["GET", "POST"])
def sign_up_step_1():
    if request.method == 'GET':
        return render_template('sign_up_step_1.html', site_key=os.environ['site_key'],
                               enable=(not session.get('enable', False)))
    captcha_response = ()
    if not session.get('enable', False):
        captcha_response = request.form['g-recaptcha-response']
    email = request.form["email"]
    res = app.session.query(User).filter_by(email=email).all()
    user_exist = len(res) != 0
    if is_human(captcha_response) and not user_exist:
        msg = EmailMessage()
        hsh = generate_password_hash(email)
        msg.set_content(f'link: http://abdulla-aby.herokuapp.com/task5/sign-up/{hsh}')
        msg['Subject'] = 'Gena na'
        msg['From'] = 'no-reply@abdulla-aby.herokuapp.com'
        msg['To'] = email
        s = smtplib.SMTP('b.li2sites.ru', 30025)
        s.send_message(msg)
        s.quit()
        app.session.add(User(email=email, password=hsh))
        app.session.commit()
        return render_template('capture_passed.html')
    else:
        return render_template('capture_failed.html')


@app.route('/task5/sign-up/<hsh>', methods=["GET", "POST"])
def sign_up_step_2(hsh):
    res = app.session.query(User).filter_by(password=hsh).all()
    if request.method == 'GET':
        if len(res) == 0:
            return redirect(url_for('sign_up_step_1'))
        return render_template('sign_up_step_2.html', url=f'/task5/sign-up/{hsh}', email=res[0].email)
    user = res[0]
    pass1 = request.form['password']
    pass2 = request.form['password2']
    correct = pass1 == pass2
    if correct:
        user.password = generate_password_hash(pass1)
        app.session.add(user)
        app.session.commit()
    return render_template('sign_up_finished.html', error=correct)


@app.route('/task5/sign-in', methods=["GET", "POST"])
def sign_in():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        res = app.session.query(User).filter_by(email=email).all()
        correct = len(res) != 0 and check_password_hash(res[0].password, password)
        if correct:
            session['logged'] = True
            time = datetime.datetime.now()
            ip = request.remote_addr
            app.session.add(Conn(email=email, time=time, ip=ip))
            app.session.commit()
            session['email'] = email
            return redirect(url_for('main'))
        else:
            return redirect(url_for('sign_in'))
    if not session.get('logged', False):
        return render_template("sign_in.html")
    else:
        return redirect(url_for('main'))


@app.route('/task5/sign-out')
def sign_out():
    session['logged'] = False
    return f"<pre>{'signed out'}</pre>"


@app.route('/task5/')
def main():
    if not session.get('logged', False):
        return redirect(url_for('sign_in'))
    email = session['email']
    user_conns = app.session.query(Conn).filter_by(email=email).order_by(desc(Conn.id)).all()
    return render_template('signed_in.html', attempts=user_conns)


@app.route('/task5/work', methods=["GET", "POST"])
def work():
    if not session.get('logged', False):
        return redirect(url_for('sign_in'))
    email = session['email']
    if request.method == 'POST':
        n = request.form['n']
        data = datetime.datetime.now()
        app.session.add(Work(time=data, n=n, status='Queued', email=email))
        app.session.commit()
    tasks = app.session.query(Work).filter_by(email=email).order_by(desc(Work.id)).all()
    return render_template('tasks.html', id="work", tasks=tasks)


@app.teardown_appcontext
def remove_session(*args, **kwargs):
    app.session.remove()


if __name__ == '__main__':
    app.run()
