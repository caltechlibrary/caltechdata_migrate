from caltechdata_write import Caltechdata_write 
#from ezid_update import update_doi
import os,glob,json,csv

path = '2014Public'

token = os.environ['TINDTOK']

sites = os.listdir(path)#=path)
outfile = open("sites.txt",'w')
counter = 266
ids = {}
for site in sites:
    outfile.write(site+','+str(counter)+'\n')
    ids[site]=counter
    counter = counter + 1

#Read in email file
infile = open("emails.csv")#,newline='')
emails = csv.reader(infile)

for site in sites:
    archived = False
    location = path+"/"+site
    aloc = path+"/"+site+"/"+"R0_archive"
    if os.path.isdir(aloc):
        archived = True
    print(site, archived)
    files = [os.path.join(location, f) for f in os.listdir(location)]
    if archived == True:
        fname = glob.glob('metadata/tccon*'+site+".R1.json")[0]
    else:
        fname = glob.glob('metadata/tccon*'+site+".R0.json")[0]
    metaf = open(fname,'r')
    metadata = json.load(metaf)
    cleaned = []
    for f in files:
        if f.split('/')[-1] != 'R0_archive':
            cleaned.append(f)
    files = cleaned
    metadata['publisher'] = "CaltechDATA"
    metadata['publicationYear'] = "2017"
    metadata['publicationDate'] = "2017-09-08"
    #pull date from file
    for f in files:
        if f.split('.')[-1]=='nc':
            fullname = f.split('/')[-1].split('.')[0]
            date = fullname[2:6]+'-'+fullname[6:8]+'-'+fullname[8:10]+\
                    '/'+fullname[11:15]+'-'+fullname[15:17]+'-'+fullname[17:19]
    for d in metadata['dates']:
        if d['dateType'] == 'Collected':
            d['date'] = date
    if 'geoLocations' in metadata:
        metadata['geoLocations'][0]['geoLocationPoint']['pointLatitude']=\
                    float(metadata['geoLocations'][0]['geoLocationPoint']['pointLatitude'])
        metadata['geoLocations'][0]['geoLocationPoint']['pointLongitude']=\
                    float(metadata['geoLocations'][0]['geoLocationPoint']['pointLongitude'])
    contributors = metadata['contributors']
    new = []
    for c in contributors:
        if c['contributorType'] == 'HostingInstitution':
            meta = {'nameIdentifiers': [{'nameIdentifierScheme': 'GRID',
                    'nameIdentifier': 'grid.20861.3d', 'schemeURI':
                    'https://www.grid.ac/institutes/'}], 'contributorName':
                    'California Institute of Techonolgy, Pasadena, CA (US)',
                    'contributorType': 'HostingInstitution'}
            new.append(meta)
        else:
            new.append(c)
    for row in emails:
            #Find email for site
            if row[0]==site:
                if len(row) == 1:
                    print("No email for "+site)
                else:
                    for author in metadata['creators']:
                        if author['familyName'] == row[2]:
                            meta = author.copy()
                            meta['contributorEmail'] = row[1]
                            meta['contributorType'] = 'ContactPerson'
                            meta['contributorName'] = meta.pop('creatorName')
                            new.append(meta)
    metadata['contributors'] = new
    #reste email list iterator
    infile.seek(0)

    related = metadata['relatedIdentifiers']
    new = []
    for r in related:
        if r['relatedIdentifier']!="http://tccon.ornl.gov/":
            new.append(r)
    if archived == True:
        newf = glob.glob('metadata/tccon*'+site+".R0.json")[0]
        newf = open(newf,"r")
        newm = json.load(newf)
        meta = {"relatedIdentifier": newm["identifier"]["identifier"],
                    "relationType": "IsNewVersionOf",
                    "relatedIdentifierType": "DOI"}
        new.append(meta)

    meta = {"relatedIdentifier":
        "https://tccon-wiki.caltech.edu/Network_Policy/Data_Use_Policy/Data_Description",
                "relationType": "IsDocumentedBy",
                "relatedIdentifierType":"URL"}
    new.append(meta)
    meta = {"relatedIdentifier": "https://tccon-wiki.caltech.edu/Sites",
                "relationType": "IsDocumentedBy",
                "relatedIdentifierType":"URL"}
    new.append(meta)
    metadata["relatedIdentifiers"] = new

    Caltechdata_write(metadata.copy(),token,files)

    #print(metadata['identifier'])

    #doi = metadata['identifier']['identifier'].encode("utf-8")

    #Strip contributor emails
    #for c in metadata['contributors']:
        #        if 'contributorEmail' in c:
                #            c.pop('contributorEmail')
    #metadata.pop('publicationDate')

    #print(doi,ids[site])
    #update_doi(doi,metadata,'https://data.caltech.edu/records/'+str(ids[site]))
        
