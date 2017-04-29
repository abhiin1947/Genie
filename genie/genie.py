from flask import Flask
from flask import render_template
import urllib2
import xmltodict
import json

app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/get_mosquitos')
def mosquitos():
    response = urllib2.urlopen('http://www.boldsystems.org/index.php/API_Public/combined?bin=BOLD:AAA5125&format=xml')
    res_string = response.read()
    result = xmltodict.parse(res_string)
    return json.dumps(result)


@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

if __name__ == '__main__':
    app.run()
