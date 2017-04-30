import xmltodict


client = MongoClient('localhost', 27017)
db = client.genie
collection = db.mosquitos


def handle_record(_, record):
    if record["bin_uri"] is not None:
        collection.insert_one(record)
        print "Inserted one record with name:" + record["bin_uri"]

    return True

if __name__ == '__main__':
    print "Fetching URL"
    print "Fetching complete"
    xmltodict.parse(open("bold_data.xml"), process_namespaces=False, item_depth=2, item_callback=handle_record)


