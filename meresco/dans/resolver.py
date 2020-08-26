from meresco.core import Observable
from meresco.xml.namespaces import namespaces
from lxml import etree
from lxml.etree import parse, XMLSchema, XMLSchemaParseError, _ElementTree, tostring, fromstring


class Resolver(Observable):

    def __init__(self, ro=True, name=None, nsMap=None):
        Observable.__init__(self, name=name)
        self._nsMap = namespaces.copyUpdate(nsMap or {})
        self._isReadOnly = ro


    def add(self, identifier, partname, lxmlNode, **kwargs):

        # TODO: Check if we need to resolve urn:nbn avaialable from DIDL-objectFile's too.

        # - Meerdere lokaties per urn:nbn per repository: JA, OVERNEMEN (in praktijk is er maar 1 per repo, maar is nodig voor provenance): Er wordt geitereerd over locaties die NIET marked DELETED zijn. De meest recente wint.
        # - Deletes van urn:nbn en bijhorende lokatie (via SRU-delete): NEE = OVERNEMEN
        # - Bij een nieuwe upload van locaties-nbn pairs voor een merescoGroup ID, worden de Locaties die reeds in database staan, maar niet meer voorkomen in de nieuwe lijst, in de database deleted voor de betreffende repository

        f_normdoc = fromstring(lxmlNode.xpath("//document:document/document:part[@name='normdoc']/text()", namespaces=self._nsMap)[0]) #TODO: import 'normdoc" string.
        f_meta = fromstring(lxmlNode.xpath("//document:document/document:part[@name='meta']/text()", namespaces=self._nsMap)[0]) #TODO: import 'normdoc" string.

        nbnlocation = f_normdoc.xpath('//didl:DIDL/didl:Item/didl:Component/didl:Resource/@ref', namespaces=self._nsMap)
        urnnbn = f_normdoc.xpath('//didl:DIDL/didl:Item/didl:Descriptor/didl:Statement/dii:Identifier/text()', namespaces=self._nsMap)[0]
        repositorygroupid = f_meta.xpath('//meta:meta/meta:repository/meta:repositoryGroupId/text()', namespaces=self._nsMap)[0]
        
        yield self.do.addNbnToDB(identifier, locations=nbnlocation, urnnbn=urnnbn, rgid=repositorygroupid, isfailover=False)
