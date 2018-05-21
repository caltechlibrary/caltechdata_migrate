from caltechdata_api import caltechdata_edit 
import os

dates = ['1914', '1933', '1935-1939', '1944-1945', '1948', '1954-1955','1957-1961', '1963', '1965-1976', '1978-1980']
locations = ['Mountain Creek','Niobrara River','American Canal','Colorado River','Hii River','Middle Loup River',
        'Rio Grande River','Canal','Atchafalaya River','Mississippi River','Red River','Rio Grande near Bernalillo, NM',
        'River, Portugal Rivers','Chop Canals','N Saskatchewan River and Elbow River',
        'South American River and Canal / Rio Magdelena and Canal de Dique','Oak Creek, Oregon','Trinity River.',
        'Rio Grande Conveyance Channel','Snake and Clearwater River','Missouri River','ACOP Canal']

idv = 943

#Get access token from TIND sed as environment variable with source token.bash
token = os.environ['TINDTOK']

metadata = {}

date_list = [{'date':'2018-05-17','dateType':'Available'}]

for d in dates:
    date_list.append({'date':d,'dateType':'Collected'})

metadata['dates'] = date_list

geolocations = []

for l in locations:
    geolocations.append({'geoLocationPlace':l})

metadata['geoLocations'] = geolocations


caltechdata_edit(token,idv,metadata,production=True)
