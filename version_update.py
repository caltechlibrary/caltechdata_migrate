from caltechdata_api import caltechdata_edit 
from caltechdata_api import caltechdata_write
from caltechdata_api import get_metadata
from update_doi import update_doi
from create_doi import create_doi
import requests
import os,glob,json,csv,subprocess,datetime,copy,argparse

path = '/data/tccon/temp'

#Switch for test or production
production = True

os.chdir(path)
token = os.environ['TINDTOK']
parser = argparse.ArgumentParser(description=\
        "update_site releases a new version of data for a TCCON site")
parser.add_argument('sid', metavar='ID', type=str,nargs='+',\
                    help='The TCCON two letter Site ID (e.g. pa for park falls)')
args = parser.parse_args()

#Read in site id file with CaltechDATA IDs
infile = open("/data/tccon/site_ids.csv")
site_ids = csv.reader(infile)
ids = {}
version = {}
for row in site_ids:
    ids[row[0]]=row[1]
    version[row[0]]=row[2]
infile.close()

outsites = []

#For each new site release
for skey in args.sid:
    #Gather information about release
    sname = \
    subprocess.check_output(['get_site_name',skey]).decode("utf-8").rstrip()
    
    new_revnum = int(version[sname].split('R')[1])+1
    new_version = 'R'+str(new_revnum)
    new_identifier = '10.14291/tccon.ggg2014.'+sname+'.'+new_version

    #First update old record
    metadata = get_metadata(ids[sname])
    orig_metadata = copy.deepcopy(metadata)

    email =\
        subprocess.check_output(['get_site_email',skey]).decode("utf-8").rstrip()
    contact =\
        subprocess.check_output(['get_site_contact',skey]).decode("utf-8").rstrip()
    contributors = metadata['contributors']
    trigger = False
    for c in contributors:
        if c['contributorType'] == 'ContactPerson':
            trigger=True
            c['contributorEmail'] = email
            c['contributorName'] = contact
    if trigger == False:
        metadata['contributors'].append({'contributorEmail':email,'contributorName':contact,'contributorType':'ContactPerson'})

    meta = {"relatedIdentifier": new_identifier,
            "relationType": "IsPreviousVersionOf",
            "relatedIdentifierType":"DOI"}
    metadata['relatedIdentifiers'].append(meta)

    r = requests.get('https://data.caltech.edu/api/record/'+ids[sname])
    exmet = r.json()['metadata']
    for f in exmet['electronic_location_and_access']:
        if f['electronic_name'][0] == 'README.txt':
            r = requests.get(f['uniform_resource_identifier'])
            readme = r.text
    outfile = open('README.txt','w')
    outfile.write('This file is obsolete.  An updated version is available at ')
    outfile.write('https://doi.org/'+new_identifier+'\n\n')
    outfile.write(readme)
    outfile.close()

    response = caltechdata_edit(token,ids[sname],copy.deepcopy(metadata),['README.txt'],[],production)
    print(response)

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

    doi = metadata['identifier']['identifier']

    #Dummy doi for testing
    if production == False:
        doi='10.5072/FK2NV9HP6P'

    #print(doi,ids[site])
    update_doi(doi,metadata,'https://data.caltech.edu/records/'+str(ids[sname]))

    #Get new file
    sitef = glob.glob(skey+'*.nc')
    if len(sitef) != 1:
        print("Cannot find public site file in /data/tccon/temp")
        exit()
    else:
        sitef = sitef[0]

    #WWork from origional metadata
    meta = {"relatedIdentifier": doi,
            "relationType":"IsNewVersionOf",
            "relatedIdentifierType":"DOI"}
    orig_metadata['relatedIdentifiers'].append(meta)
    orig_metadata['identifier']['identifier'] = new_identifier
    orig_metadata['version'] = new_version
    for t in orig_metadata['titles']:
        t['title'] = t['title'].split('.')[0]+'.'+ new_version

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
    orig_metadata['publicationDate'] = datetime.date.today().isoformat()
    for d in orig_metadata['dates']:
        if d['dateType'] == 'Collected':
            d['date'] = cred
        if d['dateType'] == 'Updated':
            d['date'] = datetime.date.today().isoformat()
        if d['dateType'] == 'Created':
            d['date'] = datetime.date.today().isoformat()
    contributors = orig_metadata['contributors']
    for c in contributors:
        if c['contributorType'] == 'ContactPerson':
            c['contributorEmail'] = email
            c['contributorName'] = contact

    response = caltechdata_write(orig_metadata,token,files,production)
    print(response)
    new_id = response.split('/')[4].split('.')[0]
    print(new_id)

    doi = new_identifier

    #Get file url
    if production == False:
        api_url = 'https://cd-sandbox.tind.io/api/record/'
    else:
        api_url = 'https://data.caltech.edu/api/record/'
    response = requests.get(api_url+new_id)
    ex_metadata = response.json()['metadata']
    for f in ex_metadata['electronic_location_and_access']:
        if f['electronic_name'][0]=='LICENSE.txt':
            url = f['uniform_resource_identifier']

    orig_metadata['rightsList'] = [{'rightsURI':url,'rights':'TCCON Data License'}]

    response = caltechdata_edit(orig_metadata,token,files,production)
    print(response)

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
    for c in orig_metadata['contributors']:
            if 'contributorEmail' in c:
                c.pop('contributorEmail')
    if 'publicationDate' in orig_metadata:
        orig_metadata.pop('publicationDate')

    #Stripping because of bad schema validator
    for t in orig_metadata['titles']:
        if 'titleType' in t:
            t.pop('titleType')

    create_doi(doi,orig_metadata,'https://data.caltech.edu/records/'+new_id)

    # Update sites file
    infile = open("/data/tccon/site_ids.csv")
    site_ids = csv.reader(infile)
    outstr = ''
    for row in site_ids:
        if row[0] == sname :
            outstr = outstr+sname+','+new_id+','+new_version+'\n'
        else:
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
for row in sites:
    if row[0] == title+' ['+sname+']':
        outstr = outstr + outsites
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
response = caltechdata_edit(token,tgz_id,copy.deepcopy(metadata),files,[],production)
print(response)

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
