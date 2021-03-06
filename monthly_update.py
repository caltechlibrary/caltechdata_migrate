from caltechdata_api import caltechdata_edit
from caltechdata_api import get_metadata
from update_doi import update_doi
from requests import session
import os,glob,json,csv,subprocess,datetime,copy

#T_FULL = {
#			'pa':'parkfalls01',
#			'oc':'lamont01',
#			'wg':'wollongong01',
#			'db':'darwin01',
#			'or':'orleans01',
#			'bi':'bialystok01',
#			'br':'bremen01',
#			'jc':'jpl01',
#			'jf':'jpl02',
#			'ra':'reunion01',
#			'gm':'garmisch01',
#			'lh':'lauder01',
#			'll':'lauder02',
#			'tk':'tsukuba02',
#			'ka':'karlsruhe01',
#			'ae':'ascension01',
#			'eu':'eureka01',
#			'so':'sodankyla01',
#			'iz':'izana01',
#			'if':'indianapolis01',
#                        'df':'edwards01',
#			'js':'saga01',
#			'fc':'fourcorners01',
#			'ci':'pasadena01',
#			'rj':'rikubetsu01',
#			'pr':'paris01',
#			'ma':'manaus01',
#			'sp':'nyalesund01',
#			'et':'easttroutlake01',
#			'an':'anmeyondo01',
#			'bu':'burgos01',
#			'we':'jena01',
#		 }

#Flag for sending to production or test
production = True

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

    #Gather information about release
    skey = sitef[0:2]
    sname =\
        subprocess.check_output(['get_site_name',skey]).decode("utf-8").rstrip()
    #sname = T_FULL[skey]
    email =\
        subprocess.check_output(['get_site_email',skey]).decode("utf-8").rstrip()
    contact =\
        subprocess.check_output(['get_site_contact',skey]).decode("utf-8").rstrip()
    # Run scrit tp generate README
    outf = open('README.txt','w')
    subprocess.run(['create_readme_contents_tccon-data',sitef],check=True,stdout=outf)
    files = {'README.txt',sitef}
    
    metadata = get_metadata(ids[sname],production)
    #Update metadata
    cred = sitef[2:6]+'-'+sitef[6:8]+'-'+sitef[8:10]+\
                    '/'+sitef[11:15]+'-'+sitef[15:17]+'-'+sitef[17:19]
    for d in metadata['dates']:
        if d['dateType'] == 'Collected':
            d['date'] = cred
        if d['dateType'] == 'Updated':
            d['date'] = datetime.date.today().isoformat()
    contributors = metadata['contributors']
    trigger = False
    for c in contributors:
        if c['contributorType'] == 'ContactPerson':
            trigger=True
            c['contributorEmail'] = email
            c['contributorName'] = contact
    if trigger == False:
        metadata['contributors'].append({'contributorEmail':email,'contributorName':contact,'contributorType':'ContactPerson'})

    #print(metadata['identifier'])
    response = caltechdata_edit(token,ids[sname],copy.deepcopy(metadata),files,['nc'],production)
    print(response)
    #outfile = open('metadata/tccon.ggg2014.'+sname+'.'+version[sname]+".json",'w')
    #outfile.write(json.dumps(metadata))

    doi = metadata['identifier']['identifier']
    for t in metadata['titles']:
        if 'titleType' not in t:
            title = t['title'].split('from')[1].split(',')[0].strip()
    split = cred.split('/')
    first = split[0]
    second = split[1]

    outsites.write(title+' ['+sname+'],https://doi.org/'+doi+','+first+','+second+'\n')
 
    #print( metadata['identifier']['identifier'].encode("utf-8"))
    if production == False:
        #Dummy doi for testing
        doi='10.5072/FK2NV9HP6P'

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

outsites.close()

#Update .tgz file
#First set the CaltechDATA Identifier for the .tgz record
tgz_id = 293
#Need to update date and file
#Still using metadata file to preserve email addresses
mfname ='/data/tccon/metadata/tccon.ggg2014.json'
metaf = open(mfname,'r')
metadata = json.load(metaf)
for d in metadata['dates']:
    if d['dateType'] == 'Updated':
        d['date'] = datetime.date.today().isoformat()
files = ['/data/tccon/temp/tccon.latest.public.tgz']
caltechdata_edit(token,tgz_id,copy.deepcopy(metadata),files,['tgz'],production)

doi = metadata['identifier']['identifier']

#Strip contributor emails
if 'contributors' in metadata:
    for c in metadata['contributors']:
        if 'contributorEmail' in c:
            c.pop('contributorEmail')
if 'publicationDate' in metadata:
    metadata.pop('publicationDate')

#Stripping because of bad schema validator
for t in metadata['titles']:
    if 'titleType' in t:
        t.pop('titleType')

if production == False:
    #Dummy doi for testing
    doi='10.5072/FK2NV9HP6P'

update_doi(doi,metadata,'https://data.caltech.edu/records/'+str(tgz_id))

if production == True:
    #Move temp files
    os.rename('/data/tccon/sites.csv','/data/tccon/old/sites.csv')
    os.rename('/data/tccon/temp/sites.csv','/data/tccon/sites.csv')
    #for mfile in glob.glob("metadata/*"):
    #    os.rename(mfile,"/data/tccon/"+mfile)
