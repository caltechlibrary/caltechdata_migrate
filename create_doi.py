import os,json
from datacite import DataCiteMDSClient, schema40


def create_doi(doi,metadata,url):

    password = os.environ['EZID_PWD']
    prefix = '10.14291'

    # Initialize the MDS client.
    d = DataCiteMDSClient(
            username='CALTECH.LIBRARY',
            password=password,
            prefix=prefix,
            #test_mode=True
            )

    assert schema40.validate(metadata)
    #Debugging if this fails
    #v = schema40.validator.validate(metadata)
    #errors = sorted(v.iter_errors(instance),key=lambda e: e.path)
    #for error in errors:
    #        print(error.message)

    xml = schema40.tostring(metadata)

    identifier = metadata['identifier']['identifier']

    d.metadata_post(xml)
    d.doi_post(identifier,url)
