This patch adds an extra column to the harvester Validatie Errors table with the description of the Validation Error itself.
Tested on: Meresco Harvester (8.1.10).

# Step 1:
Add two new files to: /usr/lib/python2.6/site-packages/meresco/harvester/controlpanel/html/dynamic

/patch1/invalid_gmh.sf
/patch1/invalidRecord_gmh.sf


# Step 2:
Create a backup of the following two files, before overwritting/applying the patched onces:
cp /usr/lib/python2.6/site-packages/meresco/harvester/controlpanel/slowfoottemplates/invalid /usr/lib/python2.6/site-packages/meresco/harvester/controlpanel/slowfoottemplates/invalid_bckp
cp /usr/lib/python2.6/site-packages/meresco/harvester/controlpanel/slowfoottemplates/showHarvesterStatus /usr/lib/python2.6/site-packages/meresco/harvester/controlpanel/slowfoottemplates/showHarvesterStatus_bckp

# Step3:
Update/overwrite two existing files:

/usr/lib/python2.6/site-packages/meresco/harvester/controlpanel/slowfoottemplates/invalid
/usr/lib/python2.6/site-packages/meresco/harvester/controlpanel/slowfoottemplates/showHarvesterStatus

with:

/patch1/invalid
/patch1/showHarvesterStatus

OR apply patches:

cd /usr/lib/python2.6/site-packages/meresco/harvester/controlpanel/slowfoottemplates
patch < /patch1/invalid.patch
patch < /patch1/showHarvesterStatus.patch
