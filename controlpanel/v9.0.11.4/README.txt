These extra files add a new WCP page that shows harvester Validation Errors table with the description of the Validation Error itself, per repositoryId.
It also publishes a link to an Excel download location. This Excel export file should be made available by the api-server however and is not included here.

Tested on: Meresco Harvester (9.0.11.4) @RHEL8

# Install:
Add two new files to: path-to-python/site-packages/meresco/harvester/controlpanel/html/dynamic

- showGmhHarvesterStatus.sf (harvester Validation Errors per repositoryId)
- pageplain.sf (Sanitzed page.sf, with no navigation. Used by the former.)

Example url:
http://your.wcp.url/showGmhHarvesterStatus?domainId=[domainId]&repositoryId=[repositoryId]