from meresco.core import Observable
import time
from meresco.dans.uiaconverter import UiaConverter
from meresco.xml.namespaces import namespaces
from lxml import etree
from lxml.etree import parse, XMLSchema, XMLSchemaParseError, _ElementTree, tostring, fromstring

# class NbnResolver(UiaConverter):
class NbnResolver(Observable):    

    def __init__(self, ro=True, name=None, nsMap=None):
        Observable.__init__(self, name=name)
        self._nsMap = namespaces.copyUpdate(nsMap or {})
        self._isReadOnly = ro


# # fromKwarg='lxmlNode', ro=False, nsMap=NAMESPACEMAP
#     def __init__(self, fromKwarg, toKwarg=None, name=None, nsMap=None, ro=True):
#         UiaConverter.__init__(self, name=name, fromKwarg=fromKwarg, toKwarg=toKwarg)
#         self._nsMap = namespaces.copyUpdate(nsMap or {})
#         self._isReadOnly = ro


    # def _convert(self, lxmlNode):
    #     if not type(lxmlNode) == _ElementTree:
    #         return lxmlNode        
    #     self._bln_success = False
    #     self._bln_hasTypOfResource = False

    #     #start conversion: Look for <part name="normdoc"> in the document:
    #     didl_tree = fromstring(lxmlNode.xpath("//document:document/document:part[@name='normdoc']/text()", namespaces=self._nsMap)[0]) #TODO: import 'normdoc" string.
    #     norm_didl_tree = self._normaliseRecord(didl_tree)



    def delete(self, identifier):
    	tombstone = '%s %s' % (identifier, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        yield self.all.add(identifier=identifier, partname="tombstone", data=tombstone)

    def add(self, identifier, partname, lxmlNode, **kwargs):
        # TODO: validate NBN against regex. ^[uU][rR][nN]:[nN][bB][nN]:[nN][lL](:([a-zA-Z]{2}))?:\\d{2}-.+
        # TODO: Strip fragments from location (#).
        # TODO: Check if location is valid URL.

        # - Meerdere lokaties per urn:nbn per repository: JA, OVERNEMEN (in praktijk is er maar 1 per repo, maar is nodig voor provenance): Er wordt geitereerd over locaties die NIET marked DELETED zijn. De meest recente wint.
        # - Deletes van urn:nbn en bijhorende lokatie (via SRU-delete): NEE = OVERNEMEN
        # - Bij een nieuwe upload van locaties-nbn pairs voor een merescoGroup ID, worden de Locaties die reeds in database staan, maar niet meer voorkomen in de nieuwe lijst, in de database deleted voor de betreffende repository

        f_normdoc = fromstring(lxmlNode.xpath("//document:document/document:part[@name='normdoc']/text()", namespaces=self._nsMap)[0]) #TODO: import 'normdoc" string.
        f_meta = fromstring(lxmlNode.xpath("//document:document/document:part[@name='meta']/text()", namespaces=self._nsMap)[0]) #TODO: import 'normdoc" string.
        # f_oairecord = fromstring(lxmlNode.xpath("//document:document/document:part[@name='record']/text()", namespaces=self._nsMap)[0]) #TODO: import 'normdoc" string.

        nbnlocation = f_normdoc.xpath('//didl:DIDL/didl:Item/didl:Component/didl:Resource/@ref', namespaces=self._nsMap)
        urnnbn = f_normdoc.xpath('//didl:DIDL/didl:Item/didl:Descriptor/didl:Statement/dii:Identifier/text()', namespaces=self._nsMap)[0]

        # harvestdate = f_meta.xpath('//meta:meta/meta:record/meta:harvestdate/text()', namespaces=self._nsMap)[0]        
        # baseurl = f_meta.xpath('//meta:meta/meta:repository/meta:baseurl/text()', namespaces=self._nsMap)[0]
        repositorygroupid = f_meta.xpath('//meta:meta/meta:repository/meta:repositoryGroupId/text()', namespaces=self._nsMap)[0]
        # repositoryid = meta.xpath('//meta:meta/meta:repository/meta:id/text()')[0]
        # oai_id = meta.xpath('//meta:meta/meta:record/meta:id/text()')[0]
        # datestamp = f_oairecord.xpath('//oai:record/oai:header/oai:datestamp/text()', namespaces=self._nsMap)[0]
        
        yield self.do.addNbnToDB(identifier, locations=nbnlocation, urnnbn=urnnbn, rgid=repositorygroupid, isfailover=False)

