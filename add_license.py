from caltechdata_write import Caltechdata_add
#from update_doi import update_doi
import os,glob,json,csv,subprocess,datetime,copy

path = '/data/tccon/temp'

os.chdir(path)
site_files = glob.glob('*.nc')
token = os.environ['TINDTOK']

outsites = open('/data/tccon/temp/sites.csv','w')

#Read in site id file with CaltechDATA IDs
infile = open("/data/tccon/site_ids.csv",newline='')
site_ids = csv.reader(infile)
ids = {}
version = {}
for row in site_ids:
    sname = row[0]
    idn=row[1]
    version=row[2]
    lic_f = open("/data/tccon/license.txt","r")
    lic = lic_f.read()
    lic = lic + subprocess.check_output(['get_site_reference',sname]).decode("utf-8").rstrip()
    outf = open('LICENSE.txt','w')
    outf.write(lic)
    outf.close()

    url = Caltechdata_add(token,idn,{},['LICENSE.txt'])
    outsites.write(sname+','+idn+','+version+','+url+'\n')

outsites.close()
