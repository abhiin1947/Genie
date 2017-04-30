from pymongo import MongoClient
import difflib
import random

client = MongoClient('localhost', 27017)
db = client.genie
collection = db.mosquitos


def find_by_nucleotide(neucleotide):
    return collection.find_one({"sequences": {"sequence": {"nucleotides": neucleotide}}})


def print_name(record):
    print record

if __name__ == "__main__":
    n = []
    l = list(collection.aggregate([
            {"$group": {"_id": "$bin_uri", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))[0]

        largest_bin = collection.find({"bin_uri": l["bin_uri"]})

        # "finland": {
        #                "latitude": 61.9241,
        #                "longitude": 25.7482,
        #                "text": {
        #                    "position": "left",
        #                    "content": "Finland"
        #                },
        #                "href": "http://en.wikipedia.org/w/index.php?search=Finland"
        #            },

        r = {
            "latitude"
        }
