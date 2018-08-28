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

collection = 'harvest_geo.ds'
if os.path.isdir(collection) == False:
    ok = dataset.init(collection)
    if ok == False:
        print("Dataset failed to init collection")
        exit()

records = {}

for h in hits['hits']['hits']:
    rid = str(h['id'])
    record = h['metadata']

    metadata = decustomize_schema(record)
    
    print(metadata['identifier']['identifier'])

    try:
        assert schema40.validate(metadata)
    except AssertionError:
        v = schema40.validator.validate(metadata)
        errors = sorted(v.iter_errors(instance), key=lambda e:e.path)
        for error in errors:
            print(error.message)
        exit()
    
    doi = metadata['identifier']['identifier']
    resolver = metadata['relatedIdentifiers'][0]['relatedIdentifier']
    title = metadata['titles'][0]['title']
    item_title = title.split(':')[0]
    item_number = title.split(':')[1].split(' ')[2]
    print(item_number)
    subjects = ''
    for s in metadata['subjects']:
        subjects = subjects + s['subject'] + ','
    subjects = subjects[0:-1]

    record = {'doi':doi,'item_title':item_title,
            'item_number':item_number,'subjects':subjects[0:-1]}
        
    result = resolver in records
    if result == False:
    
        records[resolver] = [record]

    #We need to figure out if we have a problem
    else:
        existing = records[resolver]
        new_number = record['item_number']
        error = False
        for e in existing:
            if e['item_number'] == new_number:
                if e['doi'] == '10.22002/D1.408': 
                    existing.append(record)
                    records[resolver] = existing
                elif e['doi'] == '10.22002/D1.486':
                    print("486 will be deleted")
                else:
                    error=True
                    print("Same item in CaltechDATA twice")
                    print(resolver,record['doi'],e['doi'])
                    exit()

        if error == False:
            existing.append(record)
            records[resolver] = existing

