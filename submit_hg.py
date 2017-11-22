import os,json,datetime,argparse
import requests,hglib
from caltechdata_api import caltechdata_edit
from caltechdata_api import caltechdata_write

# This script assumes that your hg repository uses tags like '2014.2'
# where the major release identifier is separated from the minor release 
# identifier by a period

# You need to get a access token from CaltechDATA
# http://libanswers.caltech.edu/faq/211307

# Requires requests and python-hglib libraries
# Requires caltechdata_api (https://github.com/caltechlibrary/caltechdata_api)

def build_relation(client,version):
    #Get url to specific tag from hg repo
    full_url = client.paths()['default'.encode('utf-8')].decode('utf-8')
    #Strip username
    split_1 = full_url.split('@')
    back = split_1[1]
    final = 'https://'+back+'/commits/tag/'+version
    return {'relatedIdentifier':final,\
            'relatedIdentifierType':'URL',\
            'relationType':'IsIdenticalTo'}

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=\
    "update_owner changes the owner of a  caltechDATA (Invenio 3) record")
    parser.add_argument('json_file',nargs=1, help=\
            'file name for json DataCite metadata file')

    args = parser.parse_args()

    token = os.environ['TINDTOK']

    history_file = '.caltechdata_written'


    already_archived = []
    archived_ids = {}
    major = set()
    if os.path.isfile(history_file):
    #This file contains versions we've already submitted
        infile = open(history_file,'r')
        for j in infile:
            line = j.rstrip()
            split = line.split(',')
            archived_version = split[0]
            ver_split = archived_version.split('.')
            major.add(ver_split[0])
            already_archived.append(archived_version)
            archived_ids[ver_split[0]]=split[1]

    repo = '.'
    client = hglib.open(repo)
    tags = client.tags()
    for t in tags:  
        version = t[0].decode('utf-8')
        if version != 'tip':
            if version not in already_archived:
                hashv = t[2]
                outfile = version+'.tgz'#open(version+'.tgz','w')
                client.archive(outfile.encode('utf-8'),hashv)
                #Determine is major or minor version
                split = version.split('.')
                mj = split[0]
                if mj not in major:
                    #New major release-New CaltechDATA record
                    #Strip username
                    metaf = open(args.json_file[0],'r')
                    metadata = json.load(metaf)
                    for d in metadata['dates']:
                        if d['dateType'] == 'Updated':
                            d['date'] = datetime.date.today().isoformat()
                    metadata['version'] = version
                    if 'relatedIdentifiers' in metadata:
                        metadata['relatedIdentifiers'].append(build_relation(client,version))
                    else:
                        metadata['relatedIdentifiers']=[build_relation(client,version)]
                    files = (outfile)
                    response = caltechdata_write(metadata,token,files,True)
                    print(response)
                    new_id = response.split('/')[4].split('.')[0]
                    outf = open(history_file,'a')
                    outf.write(version+','+new_id)
                    #Cleanup
                    os.remove(outfile)
                else:
                    #Minor release - just edit the same CaltechDATA record
                    metaf = open(args.json_file[0],'r')
                    metadata = json.load(metaf)
                    for d in metadata['dates']:
                        if d['dateType'] == 'Updated':
                            d['date'] = datetime.date.today().isoformat()
                    metadata['version'] = version
                    metadata['relatedIdentifiers'].append(build_relation(client,version))
                    files = [outfile]
                    response=caltechdata_edit(token,archived_ids[mj],metadata,files,['tgz'], True)
                    print(response)
                    #Not strictly necessary, but will prevent multiple edits
                    new_id = response.split('/')[4].split('.')[0]
                    outf = open(history_file,'a')
                    outf.write(version+','+new_id)
                    #Cleanup
                    os.remove(outfile)

