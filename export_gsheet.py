import dataset

dataset.verbose_on()
#Google sheet ID for output
output_sheet = "12Kag1F70SrkX-qDqOR9ldWx5JTIx7Nfkcn9Iy5M9Me8"
sheet_name = "Sheet1"
sheet_range = "A1:CZ"
collection = 'CompletedTheses'
client_secret = '/etc/client_secret.json'
export_list = ['.done','.key','.resolver','.subjects','.additional']
title_list = "done,key,resolver,subjects,additional"
for j in range(1,21):
    k = str(j)
    export_list.append('.identifier_'+k)
    export_list.append('.description_'+k)
    title_list = title_list+',identifier_'+k+',description_'+k
dataset.use_strict_dotpath(False)
response = dataset.export_gsheet(collection,client_secret,output_sheet,sheet_name,sheet_range,'true',dot_exprs=export_list)
print(response)
