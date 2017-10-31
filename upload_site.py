from caltechdata_write import Caltechdata_edit 
from caltechdata_write import Caltechdata_write
from update_doi import update_doi
from create_doi import create_doi
import requests
import os,glob,json,csv,subprocess,datetime,copy,argparse

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

path = '/data/tccon/temp'

#Switch for test or production
production = False

os.chdir(path)
token = os.environ['TINDTOK']
parser = argparse.ArgumentParser(description=\
        "Creates a new TCCON site")
parser.add_argument('sid', metavar='ID', type=str,nargs='+',\
                    help='The TCCON two letter Site ID (e.g. pa for park falls)')
args = parser.parse_args()

#For each new site release
for skey in args.sid:
    #Gather information about release
    sname = T_FULL[skey]
    new_version = 'R0'

    #Get new file
    sitef = glob.glob(skey+'*.nc')
    if len(sitef) != 1:
        print("Cannot find public site file in /data/tccon/temp")
        exit()
    else:
        sitef = sitef[0]

    #Re-read metadata
    mfname =\
    '/data/tccon/metadata/tccon.ggg2014.'+sname+'.'+new_version+".json"
    metaf = open(mfname,'r')
    metadata = json.load(metaf)

    #Generate new readme
    email =\
    subprocess.check_output(['get_site_email',skey]).decode("utf-8").rstrip()
    contact =\
    subprocess.check_output(['get_site_contact',skey]).decode("utf-8").rstrip()
    # Run scrit tp generate README
    outf = open('README.txt','w')
    subprocess.run(['create_readme_contents_tccon-data',sitef],check=True,stdout=outf)
    
    #Generate new license
    lic_f = open("/data/tccon/license.txt","r")
    lic_t = open("/data/tccon/license_tag.txt","r")
    lic = lic_f.read()
    lic = lic + subprocess.check_output(['get_site_reference',sname]).decode("utf-8").rstrip()
    lic = lic + '\n\n' + lic_t.read()
    outf = open('LICENSE.txt','w')
    outf.write(lic)
    outf.close()

    files = ['README.txt','LICENSE.txt',sitef]
    cred = sitef[2:6]+'-'+sitef[6:8]+'-'+sitef[8:10]+\
                    '/'+sitef[11:15]+'-'+sitef[15:17]+'-'+sitef[17:19]
    metadata['publicationDate'] = datetime.date.today().isoformat()
    metadata['publisher'] = "CaltechDATA"
    for d in metadata['dates']:
        if d['dateType'] == 'Collected':
            d['date'] = cred
        if d['dateType'] == 'Updated':
            d['date'] = datetime.date.today().isoformat()
        if d['dateType'] == 'Created':
            d['date'] = datetime.date.today().isoformat()
    contributors = metadata['contributors']
    for c in contributors:
        if c['contributorType'] == 'ContactPerson':
            c['contributorEmail'] = email
            c['contributorName'] = contact
        if c['contributorType'] == 'HostingInstitution':
            c['contributorName'] =='California Institute of Techonolgy, Pasadena, CA (US)'
    
    related = metadata['relatedIdentifiers']
    new = []
    for r in related:
        if r['relatedIdentifier']!="http://tccon.ornl.gov/":
            new.append(r)
    meta = {"relatedIdentifier":
        "https://tccon-wiki.caltech.edu/Network_Policy/Data_Use_Policy/Data_Description",
                "relationType": "IsDocumentedBy",
                "relatedIdentifierType":"URL"}
    new.append(meta)
    meta = {"relatedIdentifier": "https://tccon-wiki.caltech.edu/Sites",
                "relationType": "IsDocumentedBy",
                "relatedIdentifierType":"URL"}
    new.append(meta)
    meta = {"relatedIdentifier": "http://tccondata.org",
            "relationType": "IsPartOf",
            "relatedIdentifierType":"URL"}
    new.append(meta)
    meta = {"relatedIdentifier": "10.14291/TCCON.GGG2014",
            "relationType": "IsPartOf",
            "relatedIdentifierType":"DOI"}
    new.append(meta)
    metadata["relatedIdentifiers"] = new

    print(metadata['identifier'])
    response = Caltechdata_write(copy.deepcopy(metadata),token,files,production)
    print(response)
    new_id = response.split('/')[4].split('.')[0]
    print(new_id)

    doi = metadata['identifier']['identifier']

    for t in metadata['titles']:
        if 'titleType' not in t:
            title = t['title'].split('from')[1].split(',')[0].strip()
    split = cred.split('/')
    first = split[0]
    second = split[1]

    outsites = title+' ['+sname+'],https://doi.org/'+doi+','+first+','+second+'\n'
 
    #print( metadata['identifier']['identifier'].encode("utf-8"))
    #Dummy doi for testing
    if production == False:
        doi='10.5072/FK2NV9HP7P'

    #Strip contributor emails
    for c in metadata['contributors']:
            if 'contributorEmail' in c:
                c.pop('contributorEmail')
    if 'publicationDate' in metadata:
        metadata.pop('publicationDate')

    outfile = open('metadata/tccon.ggg2014.'+sname+'.'+new_version+".json",'w')
    outfile.write(json.dumps(metadata))

    #Stripping because of bad schema validator
    for t in metadata['titles']:
        if 'titleType' in t:
            t.pop('titleType')

    update_doi(doi,metadata,'https://data.caltech.edu/records/'+new_id)

    # Update sites file
    infile = open("/data/tccon/site_ids.csv")
    site_ids = csv.reader(infile)
    outstr = sname+','+new_id+','+new_version+'\n'
    for row in site_ids:
        outstr = outstr+','.join(row)+'\n'
    infile.close()

    if production == True:
        os.rename('/data/tccon/site_ids.csv','/data/tccon/old/site_ids.csv')
        out_id = open("/data/tccon/site_ids.csv",'w')
        out_id.write(outstr)
        out_id.close()

#Update site list - fails with multiple sites
existing = open('/data/tccon/sites.csv','r')
sites = csv.reader(existing)
outstr = ''
included = False
for row in sites:
    if row[0][0] > outsites[0] and included == False:
        outstr = outstr + outsites
        outstr = outstr + ','.join(row)+'\n'
        included = True
    else:
        outstr = outstr + ','.join(row)+'\n'
outsites = open('/data/tccon/temp/sites.csv','w')
outsites.write(outstr)
outsites.close()

#Update .tgz file
#First set the CaltechDATA Identifier for the .tgz record
tgz_id = 293
#Need to update date and file
mfname ='/data/tccon/metadata/tccon.ggg2014.json'
metaf = open(mfname,'r')
metadata = json.load(metaf)
for d in metadata['dates']:
    if d['dateType'] == 'Updated':
        d['date'] = datetime.date.today().isoformat()
files = ['tccon.latest.public.tgz']
Caltechdata_edit(token,tgz_id,copy.deepcopy(metadata),files,[],production)

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

#Dummy doi for testing
if production == False:
    doi='10.5072/FK2NV9HP6P'

update_doi(doi,metadata,'https://data.caltech.edu/records/'+str(tgz_id))

#Move temp files
if production == True:
    os.rename('/data/tccon/sites.csv','/data/tccon/old/sites.csv')
    os.rename('/data/tccon/temp/sites.csv','/data/tccon/sites.csv')
    for mfile in glob.glob("metadata/*"):
        os.rename(mfile,"/data/tccon/"+mfile)
