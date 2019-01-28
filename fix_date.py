from caltechdata_api import get_metadata,caltechdata_edit,decustomize_schema 
import requests
import os

idvs = [1163,1164,1165,1166,1167,1168,1169]

#Get access token from TIND sed as environment variable with source token.bash
token = os.environ['TINDTOK']

metadata = {}

for idv in idvs:

    api_url = "https://data.caltech.edu/api/record/"

    r = requests.get(api_url+str(idv))
    r_data = r.json()
    if 'message' in r_data:
        raise AssertionError('id '+idv+' expected http status 200, got '+r_data.status+r_data.message)
    if not 'metadata' in r_data:
        raise AssertionError('expected as metadata property in response, got '+r_data)
    metadata = r_data['metadata']

    for d in metadata['relevantDates']:
        if d['relevantDateType'] == 'created':
            d['relevantDateType'] = 'Created'

    metadata = decustomize_schema(metadata)

    response = caltechdata_edit(token,idv,metadata,production=True)
    print(response)
