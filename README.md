# caltechdata_migrate
Assorted scripts for migrating content to CaltechDATA.
These are customized for specific migrations and are likely
to need modifications to suite your needs

Require caltechdata_write.  If you're working with DOIs you'll
need datacite and if you're working with custom DOIs you'll need
ezid_update

Included scripts:

get_metadata.py - Get DataCite compliant metadata from CaltechDATA
submit_R0.py, submit_R1.py - Create a bunch of CaltechDATA records
submit_site.py - Create a single CaltechDATA record
edit_R0.py, edit_R1.py, monthly_update.py - Edit a bunch of CaltechDATA records
add_license.py - Add file to CaltechDATA records
update_license.py - Update a file in CaltechDATA records
make_table.py, update_big_license.py - Wrangle metadata
geo_files,py, harvest_geo.py - Adds geology theses plates to CaltechDATA. Requires py_dataset 0.0.68
