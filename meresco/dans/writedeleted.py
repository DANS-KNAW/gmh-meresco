from meresco.core import Observable
import time

class WriteTombstone(Observable):

    def __init__(self, name=None):
        Observable.__init__(self, name=name)

    def delete(self, identifier):
    	tombstone = '%s %s' % (identifier, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        yield self.all.add(identifier=identifier, partname="tombstone", data=tombstone)


class ResurrectTombstone(Observable):

    def __init__(self, name=None):
        Observable.__init__(self, name=name)

    def add(self, identifier, partname, **kwargs):
    	yield self.do.deletePart(identifier=identifier, partname="tombstone")
    	# return
    	# yield

# For now we can only add current datetime to tombstone, because 'datestamp' of deletion is only available from OAI-pmh delete,
# but NOT from the SRU updaterequest. Thats a pitty. Now we can only say when the record was deleted from OUR system,
# not when it was deleted from the REMOTE system.

# OAI-pmh:
    # <record status="deleted">
    #   <header>
    #     <identifier>meresco:record:3</identifier>
    #     <datestamp>1999-12-21</datestamp>
    #   </header>
    # </record>

# SRU:
	# <updateRequest>
	#     <srw:version xmlns:srw="http://www.loc.gov/zing/srw/">1.0</srw:version>
	#     <ucp:action xmlns:ucp="info:lc/xmlns/update-v1">info:srw/action/1/delete</ucp:action>
	#     <ucp:recordIdentifier xmlns:ucp="info:lc/xmlns/update-v1">meresco:record:3</ucp:recordIdentifier>
	# </updateRequest>