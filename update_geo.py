import os,subprocess,json,csv,datetime
import requests
from clint.textui import progress
from caltechdata_api import caltechdata_write
from caltechdata_api import caltechdata_edit

os.environ['GOOGLE_CLIENT_SECRET_JSON']="/etc/client_secret.json"
os.environ['DATASET']="CompletedTheses"

token = os.environ['TINDTOK']

output_sheet = "12Kag1F70SrkX-qDqOR9ldWx5JTIx7Nfkcn9Iy5M9Me8"
sheet_name = "Sheet1"
sheet_range = "A1:BI"
subprocess.run(['dataset','import-gsheet',\
                    output_sheet,sheet_name,sheet_range,'2'])

records = subprocess.check_output(["dataset","keys"],universal_newlines=True).splitlines()
for r in records:
    existing_labels = subprocess.check_output(["dataset","read",r],universal_newlines=True)
    existing_labels = json.loads(existing_labels)
    new_additional = existing_labels['additional'].replace(": Plate",": Supplement")
    for i in range(1,14):
        label = 'description_'+str(i)
        if label in existing_labels:
            l = existing_labels[label]
            split = l.split(':')
            front = split[0].replace("Supplement","Supplement "+str(i))
            new_description = front+':'+split[1]
        identifier = 'identifier_'+str(i)
        if identifier in existing_labels:
            headers = {'Accept': 'application/vnd.datacite.datacite+json'}
            print(existing_labels[identifier])
            r = requests.get(existing_labels[identifier],headers=headers)
            #print(r)
            metadata = r.json()
            new = {'title':metadata['title'].replace(": Plate",": Supplement")}
            idv = existing_labels[identifier].split('D1.')[1]
            response = caltechdata_edit(token,idv,new,{},{},False)
            print(response)
