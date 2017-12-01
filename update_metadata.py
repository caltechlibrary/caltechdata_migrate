from caltechdata_api import caltechdata_edit 
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
			'sp':'nyalesund01',
			'et':'easttroutlake01',
			'an':'anmeyondo01',
			'bu':'burgos01',
			'we':'jena01',
		 }

#Flag for sending to production or test
production = True

path = '/data/tccon/temp'

os.chdir(path)
if os.path.exists('metadata') == False:
    os.mkdir('metadata')
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

for skey in ['sp']:

    #Gather information about release
    sname = T_FULL[skey]
    email =\
        subprocess.check_output(['get_site_email',skey]).decode("utf-8").rstrip()
    contact =\
        subprocess.check_output(['get_site_contact',skey]).decode("utf-8").rstrip()
    
    #Now read in metadata file
    mfname =\
    '/data/tccon/metadata/tccon.ggg2014.'+sname+'.'+version[sname]+".json"
    metaf = open(mfname,'r')
    metadata = json.load(metaf)
    for d in metadata['dates']:
        if d['dateType'] == 'Collected':
            d['date'] = '2006-03-28/2016-09-12'
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
        metadata['contributors'].append(\
                {'contributorEmail':email,'contributorName':contact,'contributorType':'ContactPerson'})

    #print(metadata['identifier'])
    response = caltechdata_edit(token,ids[sname],copy.deepcopy(metadata),{},{},production)
    print(response)
