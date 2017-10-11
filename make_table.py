import os,glob,json,csv

path = '2014Public'

sites = os.listdir(path)#=path)

outfile = open('sites.csv','w')

for site in sites:
    archived = False
    location = path+"/"+site
    aloc = path+"/"+site+"/"+"R0_archive"
    if os.path.isdir(aloc):
        archived = True
    print(site, archived)
    files = [os.path.join(location, f) for f in os.listdir(location)]
    if archived == True:
        fname = glob.glob('metadata/tccon*'+site+".R1.json")[0]
    else:
        fname = glob.glob('metadata/tccon*'+site+".R0.json")[0]
    metaf = open(fname,'r')
    metadata = json.load(metaf)
    cleaned = []
    for f in files:
        if f.split('/')[-1] != 'R0_archive':
            cleaned.append(f)
    files = cleaned

    #pull date from file
    for f in files:
        if f.split('.')[-1]=='nc':
            fullname = f.split('/')[-1].split('.')[0]
            date = fullname[2:6]+'-'+fullname[6:8]+'-'+fullname[8:10]+\
                    '/'+fullname[11:15]+'-'+fullname[15:17]+'-'+fullname[17:19]

    doi = metadata['identifier']['identifier']
    for t in metadata['titles']:
        if 'titleType' not in t:
            title = t['title'].split('from')[1].split(',')[0].strip()
    split = date.split('/')
    first = split[0]
    second = split[1]

    outfile.write(title+' ['+site+'],https://doi.org/'+doi+','+first+','+second+'\n')
        
