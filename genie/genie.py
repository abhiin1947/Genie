from bson import ObjectId
from flask import Flask
from flask import render_template
from flask import jsonify
import urllib2
import xmltodict
import difflib
import heapq
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
    a = ""
    if "specimen_details" in x and "sex" in x["specimen_details"]:
        a += "Sex" + ("Female" if x["specimen_details"]["sex"] == "F" else "Male") + "\n"

    a += ("Site: " + x["collection_event"]["exactsite"] + "\n") if "exactsite" in x["collection_event"] else ""
    a += "Genus: Aedes \n"

    return {
        "id": str(x["_id"]),
        "latitude": float(x["collection_event"]["coordinates"]["lat"]),
        "longitude": float(x["collection_event"]["coordinates"]["lon"]),
        "text": {
            "position": "left",
            "content": x["processid"]
        },
        "nucleotide": x["sequences"]["sequence"]["nucleotides"],
        "info": a,
        "href": "http://www.boldsystems.org/index.php/Public_BarcodeCluster?clusteruri=" + x["bin_uri"]
    }


def dict_record_diff(x, main):
    a = main["sequences"]["sequence"]["nucleotides"].replace("-", "").strip()
    b = x["sequences"]["sequence"]["nucleotides"].replace("-", "").strip()

    diff = []
    for i, s in enumerate(difflib.ndiff(a, b)):
        if s[0] == ' ':
            continue
        elif s[0] == '-':
            diff.append(u'Delete {} from position {}'.format(s[-1], i))
        elif s[0] == '+':
            diff.append(u'Add {} to position {}'.format(s[-1], i))

    return {
        "id": str(x["_id"]),
        "latitude": float(x["collection_event"]["coordinates"]["lat"]),
        "longitude": float(x["collection_event"]["coordinates"]["lon"]),
        "text": {
            "position": "left",
            "content": x["processid"]
        },
        "nucleotide": x["sequences"]["sequence"]["nucleotides"].replace("-", "").strip(),
        "diff": diff,
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
        if "collection_event" in x and "coordinates" in x[
            "collection_event"] and "processid" in x and "sequences" in x and "sequence" in x[
            "sequences"] and "nucleotides" in x["sequences"]["sequence"]:
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
            if "sequences" in record and str(record["_id"]) != ido and "collection_event" in record and "coordinates" in \
                    record["collection_event"] and "specimen_identifiers" in record and "catalognum" in record[
                "specimen_identifiers"] \
                    and "sequences" in record and "sequence" in record["sequences"] and "nucleotides" in \
                    record["sequences"]["sequence"]:
                n.append(record["sequences"]["sequence"]["nucleotides"])

        c_neus = []
        for closest in difflib.get_close_matches(c["sequences"]["sequence"]["nucleotides"], n, count, cutoff=0.2):
            c_neu = find_by_nucleotide(closest)
            c_neus.append(dict_record(c_neu))

        return jsonify({"closest": c_neus, "main": dict_record(c)})
    return jsonify({})


def get_worst_matches(word, possibilities, n=3, cutoff=0.6):
    if not n > 0:
        raise ValueError("n must be > 0: %r" % (n,))
    if not 0.0 <= cutoff <= 1.0:
        raise ValueError("cutoff must be in [0.0, 1.0]: %r" % (cutoff,))
    result = []
    s = difflib.SequenceMatcher()
    s.set_seq2(word)
    for x in possibilities:
        s.set_seq1(x)
        if s.real_quick_ratio() >= cutoff >= s.quick_ratio() and s.ratio() <= cutoff:
            result.append((s.ratio(), x))

    # Move the best scorers to head of list
    result = heapq.nsmallest(n, result)
    # Strip scores for the best n matches
    return [x for score, x in result]


@app.route('/relatives/furthest/<int:count>/<ido>')
def get_relatives_furthest(count, ido):
    i = ObjectId(ido)
    c = find_object(i)
    if c is not None:

        n = []
        for record in collection.find():
            if "sequences" in record and record["_id"] != i and "collection_event" in record and "coordinates" in \
                    record["collection_event"] and "processid" in record and "sequences" in record and "sequence" in \
                    record["sequences"] and "nucleotides" in record["sequences"]["sequence"]:
                n.append(record["sequences"]["sequence"]["nucleotides"])

        furthest = get_worst_matches(c["sequences"]["sequence"]["nucleotides"], n, count, cutoff=0.8)
        f_neus = []
        for f in furthest:
            if f is not None:
                f_neu = find_by_nucleotide(f)
                f_neus.append(dict_record(f_neu))

        return jsonify({"furthest": f_neus, "main": dict_record(c)})
    return jsonify({})


if __name__ == '__main__':
    app.run(debug=True)
