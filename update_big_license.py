from caltechdata_write import Caltechdata_edit
#from update_doi import update_doi
import os,glob,json,csv,subprocess,datetime,copy

#Read in site id file with CaltechDATA IDs
infile = open("/data/tccon/site_ids.csv",newline='')
site_ids = csv.reader(infile)
ids = {}
version = {}

lic_f = open("/data/tccon/license.txt","r")
lic_t = open("/data/tccon/license_tag.txt","r")
lic = lic_f.read()

for row in site_ids:
    sname = row[0]
    idn=row[1]
    version=row[2]
    lic = lic + subprocess.check_output(['get_site_reference',sname]).decode("utf-8").rstrip()
    lic = lic + '\n\n'

lic = lic + lic_t.read()
outf = open('LICENSE.txt','w')
outf.write(lic)
outf.close()


