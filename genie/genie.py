from bson import ObjectId
from flask import Flask
from flask import render_template
from flask import jsonify
import urllib2
import xmltodict
import difflib
from pymongo import MongoClient

app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template('index.html')


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


def find_by_nucleotide(nucleotide):
    return collection.find_one({"sequences.sequence.nucleotides": nucleotide})


def dict_record(x):
    return {
        "id": str(x["_id"]),
        "latitude": float(x["collection_event"]["coordinates"]["lat"]),
        "longitude": float(x["collection_event"]["coordinates"]["lon"]),
        "text": {
            "position": "left",
            "content": x["specimen_identifiers"]["catalognum"]
        },
        "href": "http://www.boldsystems.org/index.php/Public_BarcodeCluster?clusteruri=" + x["bin_uri"]
    }


@app.route('/plots')
def get_plots():
    l = list(collection.aggregate([
        {"$group": {"_id": "$bin_uri", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))[0]

    largest_bin = collection.find({"bin_uri": l["_id"]})

    abc = []
    for x in largest_bin:
        if "collection_event" in x and "coordinates" in x["collection_event"] and "specimen_identifiers" in x and "catalognum" in x["specimen_identifiers"]\
                and "sequences" in x and "sequence" in x["sequences"] and "nucleotides" in x["sequences"]["sequence"]:
            abc.append(dict_record(x))

    return jsonify({"plots": abc})


def find_object(i):
    return collection.find_one(i)


@app.route('/relatives/closest/<int:count>/<ido>')
def get_relatives(count, ido):
    i = ObjectId(ido)
    c = find_object(i)
    if c is not None:

        n = []
        for record in collection.find():
            if "sequences" in record and str(record["_id"]) != ido and "collection_event" in record and "coordinates" in record["collection_event"] and "specimen_identifiers" in record and "catalognum" in record["specimen_identifiers"]\
                    and "sequences" in record and "sequence" in record["sequences"] and "nucleotides" in record["sequences"]["sequence"]:
                n.append(record["sequences"]["sequence"]["nucleotides"])

        c_neus = []
        for closest in difflib.get_close_matches(c["sequences"]["sequence"]["nucleotides"], n, count):
            c_neu = find_by_nucleotide(closest)
            c_neus.append(dict_record(c_neu))

        return jsonify({"closest": c_neus, "main": dict_record(c)})
    return jsonify({})


@app.route('/relatives/furthest/<int:count>/<ido>')
def get_relatives_furthest(count, ido):
    i = ObjectId(ido)
    c = find_object(i)
    if c is not None:

        n = []
        for record in collection.find():
            if "sequences" in record and record["_id"] != i and "collection_event" in record and "coordinates" in record["collection_event"] and "specimen_identifiers" in record and "catalognum" in record["specimen_identifiers"]\
                    and "sequences" in record and "sequence" in record["sequences"] and "nucleotides" in record["sequences"]["sequence"]:
                n.append(record["sequences"]["sequence"]["nucleotides"])

        furthest = list(set(n)-set(difflib.get_close_matches(c["sequences"]["sequence"]["nucleotides"], n, len(n) - count)))
        f_neus = []
        for f in furthest:
            f_neu = find_by_nucleotide(f)
            f_neus.append(dict_record(f_neu))

        return jsonify({"furthest": f_neus, "main": dict_record(c)})
    return jsonify({})

if __name__ == '__main__':
    app.run(debug=True)
