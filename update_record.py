from caltechdata_api import get_metadata,caltechdata_edit 
import os

idvs = [1163,1164,1165,1166,1167,1168,1169]

#Get access token from TIND sed as environment variable with source token.bash
token = os.environ['TINDTOK']

metadata = {}

for idv in idvs:

    metadata = get_metadata(idv)

    new_description = {'descriptionType':'Other','description':'''
    Cataloger’s note: Engel, Rene. I. Geology of the Southwest quarter of the Elsinore Quadrangle (1933). No copies [of this thesis] have ever been presented to C.I.T. The thesis has been published under the title: Geology of the Lake Elsinore Quadrangle, California (in Bulletin no. 146 of the California Division of Mines).

 …Bulletin 146, a book containing two papers: Geology and Mineral Deposits of the Lake Elsinore Quadrangle, California, prepared by Rene Engel, and Mineral Deposits of Lake Elsinore Quadrangle, California by• Rene Engel, Thomas E. Gay, Jr., and B. L. Rogers. The principal author, Dr. Engel, first began studying the geology of this area in detail in the 1920's; he has been working with it intermittently since then.</p>
 The second paper, which is primarily concerned with the economic mineral deposits of the area, was compiled by two staff members of the Division of Mines, Messrs. Gay and Rogers, working under the supervision of Dr. Engel….

 7 plates included in the Bulletin have also been scanned and included as part
 of this record.'''}

    metadata['descriptions'].append(new_description)
    metadata['dates'].append({'dateType':'Created','date':'1959'})

    response = caltechdata_edit(token,idv,metadata,production=True)
    print(response)
