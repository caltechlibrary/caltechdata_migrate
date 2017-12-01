from caltechdata_api import caltechdata_edit
from caltechdata_api import get_metadata
from update_doi import update_doi
from requests import session
import os,glob,json,csv,subprocess,datetime,copy

token = os.environ['TINDTOK']

tgz_id = 293
#Need to update date and file
mfname ='/data/tccon/metadata/tccon.ggg2014.json'
metaf = open(mfname,'r')
metadata = json.load(metaf)
#metadata = get_metadata(tgz_id,production)
for d in metadata['dates']:
        if d['dateType'] == 'Updated':
                    d['date'] = datetime.date.today().isoformat()
files = ['/data/tccon/temp/tccon.latest.public.tgz']
response = caltechdata_edit(token,tgz_id,copy.deepcopy(metadata),files,['tgz'],True)
print(response)
