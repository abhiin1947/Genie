from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/map_locations')
def map_locations():
    return render_template('map-locations.html')

if __name__ == '__main__':
    app.run()
