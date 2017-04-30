from pymongo import MongoClient
import difflib
import random

client = MongoClient('localhost', 27017)
db = client.genie
collection = db.mosquitos

if __name__ == "__main__":
    n = []
    for record in collection.find():
        if "sequences" in record and record["sequences"]["sequence"]["nucleotides"] is not None:
            n.append(record["sequences"]["sequence"]["nucleotides"])

    a = random.choice(n)
    find_by_nucleotide(a)
    for b in difflib.get_close_matches(a, n, cutoff=0.9):
        print b


def find_by_nucleotide(neucleotide):
    return collection.find_one({"sequences": {"sequence": {"nucleotides": neucleotide}}})

def print_name(record):
    print record
