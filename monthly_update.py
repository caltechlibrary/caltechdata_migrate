from caltechdata_write import Caltechdata_edit 
from update_doi import update_doi
from requests import session
import os,glob,json,csv,subprocess,datetime,copy

T_FULL = {
			'pa':'parkfalls01',
			'oc':'lamont01',
			'wg':'wollongong01',
			'db':'darwin01',
			'or':'orleans01',
			'bi':'bialystok01',
			'br':'bremen01',
			'jc':'jpl01',
			'jf':'jpl02',
			'ra':'reunion01',
			'gm':'garmisch01',
			'lh':'lauder01',
			'll':'lauder02',
			'tk':'tsukuba02',
			'ka':'karlsruhe01',
			'ae':'ascension01',
			'eu':'eureka01',
			'so':'sodankyla01',
			'iz':'izana01',
			'if':'indianapolis01',
			'df':'edwards01',
			'js':'saga01',
			'fc':'fourcorners01',
			'ci':'pasadena01',
			'rj':'rikubetsu01',
			'pr':'paris01',
			'ma':'manaus01',
			'sp':'nyaleesund01',
			'et':'easttroutlake01',
			'an':'anmeyondo01',
			'bu':'burgos01',
			'we':'jena01',
		 }

path = '/data/tccon/temp'

os.chdir(path)
site_files = glob.glob('*.nc')
token = os.environ['TINDTOK']

outsites = open('/data/tccon/temp/sites.csv','w')
api_url = api_url = "https://data.caltech.edu/api/record/"
#Read in site id file with CaltechDATA IDs
infile = open("/data/tccon/site_ids.csv")
site_ids = csv.reader(infile)
ids = {}
version = {}
for row in site_ids:
    ids[row[0]]=row[1]
    version[row[0]]=row[2]

for sitef in site_files:
    skey = sitef[0:2]
    sname = T_FULL[skey]
    email =\
    subprocess.check_output(['get_site_email',skey]).decode("utf-8").rstrip()
    contact =\
    subprocess.check_output(['get_site_contact',skey]).decode("utf-8").rstrip()
    # Run scrit tp generate README
    outf = open('README.txt','w')
    subprocess.run(['create_readme_contents_tccon-data',sitef],check=True,stdout=outf)
    files = {'README.txt',sitef}
    
    #Link to license file
    c = session()
    existing = c.get(api_url + ids[sname])
    file_info = existing.json()["metadata"]
    fids = []
    for f in files: #Check if new files match existing
        for ex in file_info["electronic_location_and_access"]:
                if 'electronic_name' in ex:
                        if ex['electronic_name'][0] == 'LICENSE.txt':
                            rights_link = ex['uniform_resource_identifier']
    mfname =\
    '/data/tccon/metadata/tccon.ggg2014.'+sname+'.'+version[sname]+".json"
    metaf = open(mfname,'r')
    metadata = json.load(metaf)
    metadata['publisher'] = "CaltechDATA"
    metadata['publicationYear'] = "2017"
    cred = sitef[2:6]+'-'+sitef[6:8]+'-'+sitef[8:10]+\
                    '/'+sitef[11:15]+'-'+sitef[15:17]+'-'+sitef[17:19]
    for d in metadata['dates']:
        if d['dateType'] == 'Collected':
            d['date'] = cred
        if d['dateType'] == 'Updated':
            d['date'] = datetime.date.today().isoformat()
    if 'geoLocations' in metadata:
        metadata['geoLocations'][0]['geoLocationPoint']['pointLatitude']=\
                    float(metadata['geoLocations'][0]['geoLocationPoint']['pointLatitude'])
        metadata['geoLocations'][0]['geoLocationPoint']['pointLongitude']=\
                    float(metadata['geoLocations'][0]['geoLocationPoint']['pointLongitude'])
    contributors = metadata['contributors']
    new = []
    metadata['rightsList'][0]['rightsURI']=rights_link
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
    meta = {'contributorEmail': email,
            'contributorType': 'ContactPerson',
            'contributorName': contact}
    new.append(meta)
    metadata['contributors'] = new
    related = metadata['relatedIdentifiers']
    new = []
    for r in related:
        if r['relatedIdentifier']!="http://tccon.ornl.gov/":
            new.append(r)
    if version[sname] != 'R0':
        newf = glob.glob('/data/tccon/metadata/tccon.ggg2014.'+sname+".R0.json")[0]
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
    meta = {"relatedIdentifier": "10.14291/TCCON.GGG2014",
            "relationType": "IsPartOf",
            "relatedIdentifierType":"DOI"}
    new.append(meta)
    meta = {"relatedIdentifier": "http://tccondata.org",
                "relationType": "IsPartOf",
                "relatedIdentifierType":"URL"}
    new.append(meta)
    metadata["relatedIdentifiers"] = new

    Caltechdata_edit(token,ids[sname],copy.deepcopy(metadata),files,['nc'])
    #print(metadata['identifier'])

    doi = metadata['identifier']['identifier']
    for t in metadata['titles']:
        if 'titleType' not in t:
            title = t['title'].split('from')[1].split(',')[0].strip()
    split = cred.split('/')
    first = split[0]
    second = split[1]

    outsites.write(title+'['+sname+'],https://doi.org/'+doi+','+first+','+second+'\n')
    
    #Need dummy doi for testing
    print( metadata['identifier']['identifier'].encode("utf-8"))
    #doi='10.5072/FK2NV9HP6P'

    #Strip contributor emails
    for c in metadata['contributors']:
            if 'contributorEmail' in c:
                c.pop('contributorEmail')
    if 'publicationDate' in metadata:
        metadata.pop('publicationDate')
    #Stripping because of bad schema validator
    for t in metadata['titles']:
        if 'titleType' in t:
            t.pop('titleType')

    #print(doi,ids[site])
    update_doi(doi,metadata,'https://data.caltech.edu/records/'+str(ids[sname]))
    
