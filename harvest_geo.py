import os,json,subprocess
import requests
from datacite import schema40
from clint.textui import progress
from caltechdata_api import decustomize_schema
import dataset

new = False

collection = 'geo_records.ds'

if new==True:
    os.system('rm -rf '+collection)

if os.path.isdir(collection) == False:
    ok = dataset.init(collection)
    if ok == False:
        print("Dataset failed to init collection")
        exit()

url = 'https://data.caltech.edu/api/records'

response = requests.get(url+'/?size=1000&q=resourceType.resourceTypeGeneral:Image')
hits = response.json()

resolver_records = []

for h in hits['hits']['hits']:
    rid = str(h['id'])
    record = h['metadata']

    metadata = decustomize_schema(record)

    assert schema40.validate(metadata)
    
    print(metadata)
    print(metadata['relatedIdentifiers'][0]['relatedIdentifier'])
    
    exit()

    result = dataset.has_key(collection,rid)

    if result == False:

        dataset.create(collection,rid, record)


    else:
        print("Duplicate record: ",rid)
