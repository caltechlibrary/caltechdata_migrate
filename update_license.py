from caltechdata_api import caltechdata_add
from caltechdata_api import caltechdata_edit
from update_doi import update_doi
import requests
import os,glob,json,csv,subprocess,datetime,copy

path = '/data/tccon/temp'

os.chdir(path)
site_files = glob.glob('*.nc')
token = os.environ['TINDTOK']

#Could break out as command line options
production = True
metadata_only = False
add = False
#Are we adding a new file - 'True' or just updating 'False'

#Read in site id file with CaltechDATA IDs
infile = open("/data/tccon/site_ids.csv",newline='')
site_ids = csv.reader(infile)
#site_ids = [['zs','744','R0']]
ids = {}
version = {}
for row in site_ids:

    sname = row[0]
    idn=row[1]
    version=row[2]

    if metadata_only == False:
        lic_f = open("/data/tccon/license.txt","r")
        lic_t = open("/data/tccon/license_tag.txt","r")
        lic = lic_f.read()
        lic = lic + subprocess.check_output(['get_site_reference',sname]).decode("utf-8").rstrip()
        lic = lic + '\n\n' +lic_t.read()
        outf = open('LICENSE.txt','w')
        outf.write(lic)
        outf.close()

        if add == True:
            caltechdata_add(token,idn,{},['LICENSE.txt'],production)
        else:
            caltechdata_edit(token,idn,{},['LICENSE.txt'],{},production)

    #Get file url
    if production == False:
        api_url = 'https://cd-sandbox.tind.io/api/record/'
    else:
        api_url = 'https://data.caltech.edu/api/record/'
    response = requests.get(api_url+idn)
    ex_metadata = response.json()['metadata']
    for f in ex_metadata['electronic_location_and_access']:
        if f['electronic_name'][0]=='LICENSE.txt':
            url = f['uniform_resource_identifier']

    metadata = {}
    metadata['rightsList'] = [{'rightsURI':url,'rights':'TCCON Data Use Policy'}]

    response = caltechdata_edit(token,idn,metadata,[],{},production)
    print(response)

    #Strip contributor emails
    if 'contributors' in metadata:
        for c in metadata['contributors']:
            if 'contributorEmail' in c:
                c.pop('contributorEmail')
    if 'publicationDate' in metadata:
        metadata.pop('publicationDate')

    #Stripping because of bad schema validator
    #for t in metadata['titles']:
    #    if 'titleType' in t:
    #        t.pop('titleType')

    #This should update monthly automatically - otherwise needs testing
    #doi = metadata['identifier']['identifier'].encode("utf-8")
    #if production == False:
        #Dummy doi for testing
        #doi='10.5072/FK2NV9HP6P'

    #update_doi(doi,metadata,'https://data.caltech.edu/records/'+idn)

