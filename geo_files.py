import os,subprocess,json,csv,datetime
import requests
from clint.textui import progress
from caltechdata_write import Caltechdata_write

# Requires Dataset
# Set up the google sheets "client_secret"  following these
# [instructions](https://github.com/caltechlibrary/dataset/blob/master/docs/dataset/import-gsheet.md)
# Set up aws 

new = False

if new == True:
    os.system("dataset init GeoThesis")

os.environ['DATASET']="GeoThesis"
os.system("dataset import-gsheet '1wbDgMdOKJYMs_1oAl5PsHDy6xfRXtlSKBxTLbOk3tfM' 'Sheet1' 'A:AW'")
os.environ['AWS_SDK_LOAD_CONFIG']="1"
token = os.environ['TINDTOK']

#Set up dictionary of thesis links
available = os.path.isfile('record_list.csv')
if available == False:
    record_list = {}
    count = 0
    keys = subprocess.check_output(["dataset","-c","s3://dataset.library.caltech.edu/CaltechTHESIS","keys"],universal_newlines=True).splitlines()
    for k in keys:
        count = count + 1
        if count % 100 == 0:
            print(count)
        metadata = subprocess.check_output(["dataset","-c","s3://dataset.library.caltech.edu/CaltechTHESIS","read",k],universal_newlines=True)
        metadata = json.loads(metadata)
        record_list[k]=metadata['official_url']
    with open('record_list.csv','w') as f:
        w = csv.writer(f)
        w.writerows(record_list.items())
else:
    record_list = {}
    reader=csv.reader(open("record_list.csv"))
    for row in reader:
        record_list[row[1]] = row[0]

#Now look at new metadata
records = subprocess.check_output(["dataset","keys"],universal_newlines=True).splitlines()
count = 0
for new in records:
    new_metadata = subprocess.check_output(["dataset","read",new],universal_newlines=True)
    new_metadata = json.loads(new_metadata)
    if new_metadata['Availability (Public or Restricted)'] == 'Public' and new_metadata['Year'] < 1978:
        record_id = record_list[new_metadata["Resolver URL"]]
        thesis_metadata =\
        subprocess.check_output(["dataset","-c","s3://dataset.library.caltech.edu/CaltechTHESIS","read",record_id],universal_newlines=True)
        thesis_metadata = json.loads(thesis_metadata)
        print(thesis_metadata)
        for file_info in thesis_metadata['documents']:

            position = file_info['pos']
            plate = 1

            if position > 1: #Ignore thesis file at position 1
                if file_info['mime_type']=='application/pdf':

                    #Download file from THESIS
                    r = requests.get(file_info["files"][0]['url'],stream=True)
                    fname = file_info["files"][0]['filename']
                    with open(fname, 'wb') as f:
                        total_length = int(r.headers.get('content-length'))
                        for chunk in \
                        progress.bar(r.iter_content(chunk_size=1024),expected_size=(total_length/1024) + 1):
                            if chunk:
                                f.write(chunk)
                        f.close()

                    plate_num = str(plate)

                    metadata = {}

                    metadata['publicationYear']=new_metadata['Year']
                    metadata['publisher']='CaltechDATA'
                    metadata['language']='en'
                    metadata['rightsList'] = [{'rights':"public-domain"},
                        {'rightsURI':'http://creativecommons.org/publicdomain/mark/1.0/'}]

                    if 'funders' in thesis_metadata:
                        funm = []
                        for f in thesis_metadata['funders']:
                            funm.append({"funderName":f['agency'],
                                "awardNumber":f['awardNumber']})
                        metadata['fundingReferences'] = funm

                    description = []
                    label = 'Plate '+plate_num+' Description'
                    if "abstract" in thesis_metadata:
                        description.append({'description':thesis_metadata['abstract'],"descriptionType":"Abstract"})
                    else:
                        description.append({'description':new_metadata[label],"descriptionType":"Other"})
                    metadata['descriptions']=description
                    metadata['titles']=[{"title":new_metadata[label]+\
                        ': Plate '+plate_num+' from "'+thesis_metadata['title']+'" (Thesis)'}]
                    
                    creators = []
                    for c in thesis_metadata['creators']:
                        name = c['family']+', '+c['given']
                        if 'orcid' in c:
                            creators.append({'creatorName':name\
                                ,'affiliations':["California Institute of Technology"],\
                                "nameIdentifiers":[{"nameIdentifer":c['orcid'],\
                                "nameIdentifierScheme":"Orcid"}]})
                        else:
                            creators.append({'creatorName':name\
                                ,'affiliations':["California Institute of Technology"]})
                    metadata['creators'] = creators

                    metadata['formats'] = ['application/pdf']
                    
                    dates = []
                    label = 'Plate '+plate_num+' Dates Collected YEAR-MONTH-DAY'
                    if label in new_metadata:
                        if new_metadata[label] != '' or ' ':
                            if type(new_metadata[label]) == str:
                                for d in new_metadata[label].split(';'):
                                    dates.append({"date":d,"dateType":"Collected"})
                            else:
                                dates.append({"date":new_metadata[label],"dateType":"Collected"})
                    dates.append({"date":datetime.date.today().isoformat(),"dateType":"Issued"})
                    if 'thesis_defense_date' in thesis_metadata:
                        dates.append({"date":thesis_metadata['thesis_defense_date'],"dateType":"Accepted"})
                    metadata['dates'] = dates

                    sub = []
                    subjects = new_metadata['Keywords'].split(',')
                    for s in subjects:
                        sub.append({"subject":s})
                    sub.append({"subject":'gps'})
                    sub.append({"subject":'thesis'})
                    metadata['subjects'] = sub

                    metadata['resourceType'] = {'resourceTypeGeneral':'Image'}

                    metadata['relatedIdentifiers'] =\
                            [{'relatedIdentifierType':"URL",\
                            "relatedIdentifier":new_metadata["Resolver URL"],\
                            "relationType":"IsSupplementTo"}]

                    geolocations = []
                    label = 'Plate '+plate_num+\
                    ' Geolocation [Lat,Long] or {[Lat,Long],[Lat,Long],... }'
                    if label in new_metadata:
                        print("GEO")
                        input_geo = new_metadata[label]
                        if '{' in input_geo:
                            input_geo = input_geo.replace("{","")
                            input_geo = input_geo.replace("}","")
                            points = input_geo.split('],[')
                            if len(points) == 4:
                                lat = set()
                                lon = set()
                                for p in points:
                                    cleaned = p.replace("[","")
                                    cleaned = cleaned.replace("]","")
                                    split = cleaned.split(',')
                                    lat.add(split[0])
                                    lon.add(split[1])
                                #guess
                                south = float(lat.pop())
                                north = float(lat.pop())
                                if north < south:
                                    s = north
                                    north = south
                                    south = s
                                east = float(lon.pop())
                                west = float(lon.pop())
                                if east < west:
                                    w = east
                                    east = west
                                    west = w
                                geolocations.append({'geoLocationBox':{\
                                    'westBoundLongitude':west,'eastBoundLongitude':east,\
                                    'southBoundLatitude':south,'northBoundLatitude':north}})

                            elif len(points) == 1:
                                cleaned = points.replace("[","")
                                cleaned = cleaned.replace("]","")
                                split = cleaned.split(',')
                                geolocations.append({"geoLocationPoint":{\
                                    "pointLatitude":split[0],"pointLongitude":split[1]}})
                            else:
                                print("TOM has not written this case",points)
                        elif input_geo != ' ' or '':
                            geolocations.append({'geoLocationPlace':input_geo})
                    print(geolocations)
                    metadata['geoLocations']=geolocations
                    
                    contributors = []
                    contributors.append({'contributorName':\
                        'California Institute of Technology',
                        "nameIdentifiers":[{'nameIdentifier':"grid.20861.3d",\
                                'nameIdentifierScheme':'GRID'}],\
                        "contributorType": "HostingInstitution"})
                    contributors.append({'contributorName':'Diaz, Tony',\
                            "contributorType":"DataCurator"})
                    metadata['contributors'] = contributors

                    response = Caltechdata_write(metadata,token,fname,False)
                    print(response)
                    plate = plate + 1
        #num_files = len(thesis_metadata['documents'])
        #for f in range(num_files-1) #We're ignoting the thesis at position 

        print(">new")
        print(new_metadata)

        #Need to record completed theses

        count = count + 1
        if count == 1:
            exit()

