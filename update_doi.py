import os,json
from datacite import DataCiteMDSClient, schema40
from EZID import EZIDClient


def update_doi(doi,metadata,url):

    SERVER = "https://ezid.cdlib.org"
    ez=EZIDClient(SERVER,
    credentials={'username':os.environ['EZID_USER'],
    'password':os.environ['EZID_PWD']})
    sid = ez.login()

    assert schema40.validate(metadata)
    #Debugging if this fails
    #v = schema40.validator.validate(metadata)
    #errors = sorted(v.iter_errors(instance), key=lambda e: e.path)
    #for error in errors:
    #        print(error.message)

    xml = schema40.tostring(metadata)

    #should verify that doi is in the form 10.xxx
    resp = ez.update('doi:'+doi,{'datacite':xml})
    print(resp)
    resp = ez.update('doi:'+doi,{'_target':url})
    print(resp)

#resp = ez.mint('doi:10.5072/FK2', {'datacite':xml})
#resp = ez.mint('doi:10.5072/FK2',{'datacite.title': 'test title',
#        'datacite.creator': 'mer','datacite.publisher':
#        'CD','datacite.publicationyear':'2017','datacite.resourcetype':'Dataset'})
#print(resp)

#resp = ez.update(doi,{'_target':head+dsplit[2].lower()})

