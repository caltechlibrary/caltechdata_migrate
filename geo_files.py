import os,subprocess,json,csv,datetime
import requests
from clint.textui import progress
from caltechdata_api import caltechdata_write
from caltechdata_api import caltechdata_edit
import dataset
# Requires Dataset
# Set up the google sheets "client_secret"  following these
# [instructions](https://github.com/caltechlibrary/dataset/blob/master/docs/dataset/import-gsheet.md)
# Set up aws 

collection="GeoThesis.ds"
os.system("rm -rf "+collection)
dataset.init(collection)

client_secret="/etc/client_secret.json"

print("Importing")

collection="GeoThesis.ds"
sheet = '1Wf4npmEWucCPJ-Ly1Vr6fzZvo1Y_kz7iTahmV9UmVHE'
err = dataset.import_gsheet(collection,sheet,'Sheet1',3,'A:CZ')
print(err)

print("Imported")

token = os.environ['TINDTOK']

#Set up dictionary of thesis links
available = os.path.isfile('data/record_list.csv')
if available == False:
    print("You need to run update_thesis_file.py")
    exit()
else:
    record_list = {}
    reader=csv.reader(open("data/record_list.csv"))
    for row in reader:
        record_list[row[1]] = row[0]

#If we want to replace a record, put number here
records_to_edit = []

#Connection to CaltechTHESIS
username = os.environ['EPUSER']
password = os.environ['EPPASSWD']
url ='https://'+username+':'+password+'@thesis.library.caltech.edu/rest/eprint/'

#Now look at new metadata
harvest_collection = 'harvest_geo.ds'
records= dataset.keys(collection)
count = 0
for new in records:
    print("Running")
    new_metadata,err = dataset.read(collection,new)
    if err != '':
        print(err)
    check_key = new_metadata['Resolver URL']
    completed = dataset.has_key(harvest_collection,new)
    if completed == False and new_metadata['Availability (Public or Restricted)'] == 'Public' and new_metadata['Year'] < 1978:
        #print(len(record_list))
        record_id = record_list[new_metadata["Resolver URL"]]
        #print(record_id)
        thesis_metadata = subprocess.check_output(["eputil",'-json',url+record_id+'.xml'],universal_newlines=True)
        thesis_metadata = json.loads(thesis_metadata)
        thesis_metadata = thesis_metadata['eprint'][0]
        output_metadata = {}
        output_text = 'Supplemental Files Information:\n'
        plate = 1
        #If placement is present, order by placement.
        #Otherwise order by position
        file_list = thesis_metadata['documents']
        pdf_files = []
        for file_info in file_list:
            if file_info['mime_type']=='application/pdf':
                if file_info['security']=='public':
                    pdf_files.append(file_info)

        #print(pdf_files)
        if 'placement' in pdf_files[0]:
            pdf_files.sort(key=lambda k: k['placement'])
        else:
            pdf_files.sort(key=lambda k: k['pos'])
    
        position = 0
        for file_info in pdf_files:
                position = position + 1
                if position > 1: #Ignore thesis file at position 1
                        #Download file from THESIS
                        r = requests.get(file_info["files"][0]['url'],stream=True)
                        fname = file_info["files"][0]['filename']
                        split = fname.split('.')
                        if split[1] == 'PDF':
                            fname = split[0]+'.pdf'
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
                        metadata['rightsList'] = [{'rights':"public-domain",
                        'rightsURI':'http://creativecommons.org/publicdomain/mark/1.0/'}]
                        #metadata['rightsList'] = [{'rights':"other",
                        #    'rightsURI':'https://data.caltech.edu/caltechthesis-license'}]

                        if 'funders' in thesis_metadata:
                            print(thesis_metadata['funders'])
                            funm = []
                            for f in thesis_metadata['funders']['items']:
                                if 'awardNumber' in f:
                                    funm.append({"funderName":f['agency'],
                                    "awardNumber":f['awardNumber']})
                                else:
                                    funm.append({"funderName":f['agency']})
                            metadata['fundingReferences'] = funm

                        description = []
                        label = 'Plate '+plate_num+' Description'
                        if "abstract" in thesis_metadata:
                            description.append({'description':thesis_metadata['abstract'],"descriptionType":"Abstract"})
                        else:
                            description.append({'description':new_metadata[label],"descriptionType":"Other"})
                        metadata['descriptions']=description
                        title = new_metadata[label]+': Supplement '+plate_num+' from "'+thesis_metadata['title']+'" (Thesis)'
                        metadata['titles']=[{"title":title}]
                        output_metadata['description_'+plate_num]="Supplement "+plate_num+" in CaltechDATA: "+new_metadata[label]
                        output_text = output_text + title +'\n'

                        creators = []
                        for c in thesis_metadata['creators']['items']:
                            n = c['name']
                            name = n['family']+', '+n['given']
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
                        metadata['version'] = '1.0'

                        dates = []
                        label = 'Plate '+plate_num+' Dates Collected YEAR-MONTH-DAY'
                        if label in new_metadata:
                            if new_metadata[label] not in{'',' '}:
                                if type(new_metadata[label]) == str:
                                    for d in new_metadata[label].split(';'):
                                        dates.append({"date":d,"dateType":"Collected"})
                                else:
                                    dates.append({"date":new_metadata[label],"dateType":"Collected"})
                                output_text = output_text + 'Date(s) Collected: '+str(new_metadata[label])+'\n'
                        dates.append({"date":datetime.date.today().isoformat(),"dateType":"Issued"})
                        if 'thesis_defense_date' in thesis_metadata:
                            dates.append({"date":thesis_metadata['thesis_defense_date'],"dateType":"Accepted"})
                        if 'datestamp' in thesis_metadata:
                            datev = thesis_metadata['datestamp'].split(' ')[0]
                            dates.append({"date":datev,"dateType":"Available"})
                        metadata['dates'] = dates

                        sub = []
                        output_metadata['subjects']= new_metadata['Keywords']
                        subjects = new_metadata['Keywords'].split(',')
                        for s in subjects:
                            if s not in {'',' '}:
                                sub.append({"subject":s.strip()})
                        sub.append({"subject":'gps'})
                        sub.append({"subject":'thesis'})
                        if 'thesis_type' in thesis_metadata:
                            sub.append({"subject":thesis_metadata['thesis_type']})
                        metadata['subjects'] = sub

                        metadata['resourceType'] = {'resourceTypeGeneral':'Image'}

                        metadata['relatedIdentifiers'] =\
                            [{'relatedIdentifierType':"URL",\
                            "relatedIdentifier":new_metadata["Resolver URL"],\
                            "relationType":"IsSupplementTo"}]
                        output_metadata['resolver']=new_metadata["Resolver URL"]

                        geolocations = []
                        label = 'Plate '+plate_num+\
                        ' Geolocation [Lat,Long] or {[Lat,Long],[Lat,Long],... }'
                        if label in new_metadata:
                            input_geo = new_metadata[label]
                            if '[' in input_geo:
                                if '{' in input_geo:
                                    input_geo = input_geo.replace("{","")
                                    input_geo = input_geo.replace("}","")
                                points = input_geo.split('],[')
                                if len(points) == 4:
                                    lat = []
                                    lon = []
                                    for p in points:
                                        cleaned = p.replace("[","")
                                        cleaned = cleaned.replace("]","")
                                        split = cleaned.split(',')
                                        lat.append(float(split[0]))
                                        lon.append(float(split[1]))
                                    south = sorted(lat).pop(0)
                                    north = sorted(lat).pop()
                                    east = sorted(lon).pop()
                                    west = sorted(lon).pop(0)
                                    geolocations.append({'geoLocationBox':{\
                                    'westBoundLongitude':west,'eastBoundLongitude':east,\
                                    'southBoundLatitude':south,'northBoundLatitude':north}})
                                    output_text = output_text + \
                                        'Geographic Location Bounding Box: '\
                                    +str(east)+' Degrees East; '\
                                    +str(west)+' Degrees West; '\
                                    +str(north)+' Degrees North; '\
                                    +str(south)+' Degrees South \n'

                                elif len(points) == 1:
                                    point = points[0]
                                    cleaned = point.replace("[","")
                                    cleaned = cleaned.replace("]","")
                                    split = cleaned.split(',')
                                    geolocations.append({"geoLocationPoint":{\
                                    "pointLatitude":float(split[0]),"pointLongitude":float(split[1])}})
                                    output_text = output_text + \
                                        'Geographic Location Point: '\
                                        +str(split[0])+' Degrees Latitude; '\
                                        +str(split[1])+' Degrees Longitude \n'
                                else:
                                    #We're handling the rest as groups of
                                    #points instead of polygons
                                    for p in points:
                                        geoa = []
                                        cleaned = p.replace("[","")
                                        cleaned = cleaned.replace("]","")
                                        split = cleaned.split(',')
                                        geolocations.append({"geoLocationPoint":{\
                                        "pointLatitude":float(split[0]),"pointLongitude":float(split[1])}})
                                        output_text = output_text + \
                                        'Geographic Location Point: '\
                                        +str(split[0])+' Degrees Latitude; '\
                                        +str(split[1])+' Degrees Longitude \n'

                            elif input_geo not in {' ',''}:
                                geolocations.append({'geoLocationPlace':input_geo})
                                print("WRITING GEO PLACE FOR>"+input_geo+"<HERE")
                                output_text = output_text + \
                                    'Geographic Location Place: '+input_geo+' ' 
                    
                        if geolocations != []:
                            print(geolocations)
                            metadata['geoLocations']=geolocations
                    
                        contributors = []
                        contributors.append({'contributorName':\
                        'California Institute of Technology',
                        "nameIdentifiers":[{'nameIdentifier':"grid.20861.3d",\
                                'nameIdentifierScheme':'GRID'}],\
                        "contributorType": "HostingInstitution"})
                        contributors.append({'contributorName':'Diaz, Tony',\
                            "nameIdentifiers":[{'nameIdentifier':"0000-0002-4338-4775",\
                                'nameIdentifierScheme':'ORCID'}],\
                            "contributorType":"DataCurator"})
                        metadata['contributors'] = contributors

                        if records_to_edit != []:
                            idv = records_to_edit.pop(0)
                            print(fname)
                            response = caltechdata_edit(token,idv,metadata,fname,{'pdf'},True)
                            print(response)
                        else:
                            print(fname)
                            response = caltechdata_write(metadata,token,fname,True)
                            print(response)

                        plate = plate + 1

        count = count + 1

        #Neet to run harvest_geo.py to not re-write existing records
