from flask import Flask
from flask import render_template
from flask import jsonify
import urllib2
import xmltodict
from pymongo import MongoClient

app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/map_locations')
def map_locations():
    return render_template('map-locations.html')


@app.route('/map_species')
def map_species():
    return render_template('map-species.html')


@app.route('/get_mosquitos')
def mosquitos():
    response = urllib2.urlopen('http://www.boldsystems.org/index.php/API_Public/combined?bin=BOLD:AAA5125&format=xml')
    res_string = response.read()
    result = xmltodict.parse(res_string)
    return jsonify(result)


@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


client = MongoClient('localhost', 27017)
db = client.genie
collection = db.mosquitos


@app.route('/plots')
def get_plots():
    l = list(collection.aggregate([
        {"$group": {"_id": "$bin_uri", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))[0]

    largest_bin = collection.find({"bin_uri": l["_id"]})

    abc = []
    for x in largest_bin:
        if "collection_event" in x and "coordinates" in x["collection_event"] and "specimen_identifiers" in x and "catalognum" in x["specimen_identifiers"]:
            r = {
                "latitude": float(x["collection_event"]["coordinates"]["lat"]),
                "longitude": float(x["collection_event"]["coordinates"]["lon"]),
                "text": {
                    "position": "left",
                    "content": x["specimen_identifiers"]["catalognum"]
                },
                "href": "http://www.boldsystems.org/index.php/Public_BarcodeCluster?clusteruri=" + x["bin_uri"]
            }
            abc.append(r)

    return jsonify({"plots": abc})


if __name__ == '__main__':
    app.run(debug=True)
