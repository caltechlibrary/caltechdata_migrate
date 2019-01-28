import os,json,subprocess
import requests
from datacite import schema40
from clint.textui import progress
from caltechdata_api import decustomize_schema
from operator import attrgetter
import dataset

def get_num(record):
    return record['item_number']

orig_collection="GeoThesis.ds"
sheet = '1Wf4npmEWucCPJ-Ly1Vr6fzZvo1Y_kz7iTahmV9UmVHE'
err = dataset.import_gsheet(orig_collection,sheet,'Sheet1',3,'A:CZ')
if err != '':
    print(err)
    exit()

collection = 'harvest_geo.ds'

#Nothing in this collection gets saved
if os.path.isdir(collection) == True:
    os.system('rm -rf '+collection)

ok = dataset.init(collection)
if ok == False:
    print("Dataset failed to init collection")
    exit()

url = 'https://data.caltech.edu/api/records'

response = requests.get(url+'/?size=1000&q=resourceType.resourceTypeGeneral:Image')
hits = response.json()

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
    item_title = title.split(': Supplement ')[0]
    #print(title)
    item_number = title.split(': Supplement ')[1].split(' ')[0]
    #print(item_number)
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

    origional,err = dataset.read(orig_collection,resolver)
    if err != '':
        print(err)
    if 'Linked' in origional:
        linked = origional['Linked']
    else:
        linked = ''

    record = {'doi':doi,'item_title':item_title,'title':title,
            'item_number':item_number,'subjects':subjects,
            'dates':dates,'geo':geo,'linked':linked}
        
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
                error=True
                print("Same item in CaltechDATA twice")
                print(resolver,record['doi'],e['doi'])

        if error == False:
            existing.append(record)
            records[resolver] = existing

for resolver in records:
    record = records[resolver]
    output = {'resolver':resolver}
    output_str = 'Supplemental Files Information:\n'
    #print(record)
    record = sorted(record, key=get_num)
    #print(record)
    for r in record:
        output['identifier_'+r['item_number']] = 'https://doi.org/' + r['doi']
        start_str = 'Supplement '+r['item_number']+' in CaltechDATA: '
        output['description_'+r['item_number']] = start_str + r['item_title'] 
        output_str = output_str + r['title']+'\n'
        if r['dates'] != '':
            output_str = output_str + 'Date(s) Collected: ' +r['dates']+'\n'
        if r['geo'] != '':
            output_str = output_str + r['geo']
        output['subjects'] = r['subjects']
        output['linked'] = r['linked']
    output['additional'] = output_str
    dataset.create(collection,resolver,output)

#Google sheet export
output_sheet = '1vhw4cz2txRlY5iWRhQveOs4nk-4aW6FMZKbDOX6cgu0'
sheet_name = "Sheet1"
sheet_range = "A1:CZ"
client_secret = '/etc/client_secret.json'
export_list = ['.linked','.resolver','.subjects','.additional']
for j in range(1,21):
    k = str(j)
    export_list.append('.identifier_'+k)
    export_list.append('.description_'+k)
dataset.use_strict_dotpath(False)
keys = dataset.keys(collection)
dataset.frame(collection,'exportf',keys,export_list)
response = dataset.export_gsheet(collection,'exportf',output_sheet,sheet_name,sheet_range)
print("Export: ",response)

