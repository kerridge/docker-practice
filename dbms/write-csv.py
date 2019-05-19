import csv
from datetime import datetime
import firebase_admin
import google.cloud
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceCredentials.json")
firebase_admin.initialize_app(cred)

# firestore connection
store = firestore.client()

# csv path and name of firestore collection to create
# file_path = "data-subsets/business-owners-subset-utf-8.csv"
# collection_name = "business-owners"

file_path = "data-subsets/business-licences-subset-utf-8.csv"
collection_name = "business-licences"


# basically a method to stop the whole csv from being loaded into memory
# and to batch transactions together
def batch_data(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


def attemptParse(item):

    # 2000-12-18T00:00:00 // expected date format
    # if it is 19 chars long and capital 'T' is 11th char
    if len(item) == 19 and item[10] == 'T':
        try:
            # a strftime safe char
            item = item.replace('T', ' ')
            # format string to date-string
            item = datetime.strptime(item, '%Y-%m-%d %H:%M:%S')
            # # parse date-string to datetime obj
            # item = datetime.strftime(s, '%Y-%m-%d %H:%M:%S')
        except:
            print('ERROR: could not parse datetime')
            pass
    

    return item


# data to return
data = []
# our list of csv coulmn headers to be extracted
headers = []

with open(file_path) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        # extract the line headers
        if line_count == 0:
            for header in row:
                headers.append(header)
            line_count += 1
        else:
            obj = {}
            for idx, item in enumerate(row):
                # apply any transformations to `item` here

                # dont write the object if null, NoSQL benefits
                if item != "":
                    # attempt to parse object to other types
                    item = attemptParse(item)

                    # headers[idx] gives us the header for the current column
                    # e.g. 'DATE ISSUED'
                    # could be useful if we transform column names meaningfully

                    # save item to json
                    obj[headers[idx]] = item


            data.append(obj)
            line_count += 1
    print(f'Processed {line_count} lines.')


# loop through and write data to firestore
# a batch is a set of transactions that have been grouped together
for batched_data in batch_data(data, 499):
    batch = store.batch()
    for data_item in batched_data:
        # grab our document reference object
        doc_ref = store.collection(collection_name).document()
        batch.set(doc_ref, data_item)
    batch.commit()

print('Done')