import os,subprocess,json,csv,datetime
import requests
from clint.textui import progress
from caltechdata_api import caltechdata_write
from caltechdata_api import caltechdata_edit

os.environ['DATASET']="CompletedTheses"

token = os.environ['TINDTOK']


records = subprocess.check_output(["dataset","keys"],universal_newlines=True).splitlines()
for r in records:
    existing_labels = subprocess.check_output(["dataset","read",r],universal_newlines=True)
    existing_labels = json.loads(existing_labels)
    for i in range(1,14):
        identifier = 'identifier_'+str(i)
        if identifier in existing_labels:
            #headers = {'Accept': 'application/vnd.datacite.datacite+json'}
            #req = requests.get(existing_labels[identifier],headers=headers)
            #print(r)
            #metadata = req.json()
            new = {'rightsList':[{'rights':'public-domain','rightsURI':'http://creativecommons.org/publicdomain/mark/1.0/'}]}
            idv = existing_labels[identifier].split('D1.')[1]
            response = caltechdata_edit(token,idv,new,{},{},True)
            print(response)

