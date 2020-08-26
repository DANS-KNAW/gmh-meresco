# -*- coding: utf-8 -*-
# Following may be used to count/iter over the identifiers stored in the OAI-pmh Berkeley DB.
# 
# This runs from python command line only?
# Not from a .py file?? Why? I don't know...

from bsddb import btopen

db = btopen('identifier2setSpecs.bd', 'r')

print "LAST DB record:", db.last()

print 'Total Records:', len(db.items())

for k, v in db.iteritems():
    print k, v
    
cnt = 0
for k, v in db.iteritems():
    if v.find('dataset') == -1:
        cnt = cnt + 1
print cnt
