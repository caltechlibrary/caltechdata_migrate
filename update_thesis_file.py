import os,subprocess,json

record_list = {}
count = 0
url = 'https://thesis.library.caltech.edu/rest/eprint/'
keys = subprocess.check_output(["eputil",'-json',url])
#keys = keys.split('/n')
username = os.environ['EPUSER']
password = os.environ['EPPASSWD']
url =\
'https://'+username+':'+password+'@thesis.library.caltech.edu/rest/eprint/'
for k in keys:
        count = count + 1
        if count % 100 == 0:
            print(count)
        metadata =\
        subprocess.check_output(["eputil",'-json',url+str(k)+'.xml'],universal_newlines=True)
        metadata = json.loads(metadata)
        if metadata != {}:
            record_list[k]=metadata['eprint'][0]['official_url']
        else:
            print("Bad Record: "+k)
            print(metadata)
with open('record_list.csv','w') as f:
    w = csv.writer(f)
    w.writerows(record_list.items())
