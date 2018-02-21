from caltechdata_api import caltechdata_edit 
from update_doi import update_doi
from requests import session
import os,glob,json,csv,subprocess,datetime,copy

infile = open('/data/tccon/sites.csv','r')
site_ids = csv.reader(infile)
dois = []
for row in site_ids:
    doi = row[1].split('doi.org')[1][1:]
    dois.append(doi)

related = [{"relatedIdentifier":"10.14291/tccon.ggg2014.documentation.R0/1221662",
            "relatedIdentifierType": "DOI",
            "relationType": "IsDocumentedBy"}]
for d in dois:
    related.append({"relatedIdentifier":d,
        "relatedIdentifierType": "DOI",
        "relationType": "HasPart"})

idv = "10.14291/tccon.archive/1348407"

infile = open('/data/tccon/metadata/tccon.archive','r')
metadata = json.load(infile)

metadata['relatedIdentifiers']= related

print(metadata)

update_doi(idv,metadata,'http://tccondata.org')
