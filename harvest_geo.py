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
    dates = ''
    for d in metadata['dates']:
        if d['dateType'] == 'Collected':
            dates = dates + d['date'] +','
    dates = dates[0:-1]
    geo = ''
    if 'geoLocations' in metadata:
        loc = metadata['geoLocations']
        for g in loc:
            if 'geoLocationBox' in g:
                box = g['geoLocationBox']
                geo = geo + 'Geographic Location Bounding Box: '\
                + str(box['eastBoundLongitude']) + ' Degrees East; '\
                + str(box['westBoundLongitude']) + ' Degrees West; '\
                + str(box['northBoundLatitude']) + ' Degrees North; '\
                + str(box['southBoundLatitude']) + ' Degrees South\n'
            if 'geoLocationPoint' in g:
                box = g['geoLocationPoint']
                geo = geo + 'Geographic Location Point: '\
                + str(box['pointLongitude']) + ' Degrees Longitude; '\
                + str(box['pointLatitude']) + ' Degrees Latitude\n'
            if 'geoLocationPlace' in g:
                geo = geo + 'Geographic Location Place: '+g['geoLocationPlace']

    record = {'doi':doi,'item_title':item_title,'title':title,
            'item_number':item_number,'subjects':subjects,
            'dates':dates,'geo':geo}
        
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

for resolver in records:
    record = records[resolver]
    output = {'resolver':resolver}
    output_str = 'Supplemental Files Information:\n'
    for r in record:
        output['identifier_'+r['item_number']] = r['doi']
        start_str = 'Supplement '+r['item_number']+' in CaltechDATA: '
        output['description_'+r['item_number']] = start_str + r['item_title'] 
        output_str = output_str + r['title']+'\n'
        if r['dates'] != '':
            output_str = output_str + 'Date(s) Collected: ' +r['dates']
        if r['geo'] != '':
            output_str = output_str + geo
        output['subjects'] = r['subjects']
    output['additional'] = output_str
    dataset.create(collection,resolver,output)

#Google sheet export
output_sheet = '1vhw4cz2txRlY5iWRhQveOs4nk-4aW6FMZKbDOX6cgu0'
sheet_name = "Sheet1"
sheet_range = "A1:CZ"
client_secret = '/etc/client_secret.json'
export_list = ['.resolver','.subjects','.additional']
for j in range(1,21):
    k = str(j)
    export_list.append('.identifier_'+k)
    export_list.append('.description_'+k)
dataset.use_strict_dotpath(False)
response = dataset.export_gsheet(collection,client_secret,output_sheet,sheet_name,sheet_range,'true',dot_exprs=export_list)
print("Export: ",response)

