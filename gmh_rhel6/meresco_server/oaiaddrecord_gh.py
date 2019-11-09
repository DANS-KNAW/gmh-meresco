## begin license ##
# 
# "Meresco Oai" are components to build Oai repositories, based on
# "Meresco Core" and "Meresco Components". 
# 
# Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
# Copyright (C) 2009 Tilburg University http://www.uvt.nl
# Copyright (C) 2010-2012 Stichting Kennisnet http://www.kennisnet.nl
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
# 
# This file is part of "Meresco Oai"
# 
# "Meresco Oai" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "Meresco Oai" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "Meresco Oai"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

from meresco.core import Transparent, asyncreturn
from lxml.etree import parse, _ElementTree, tostring, iselement
from lxml import etree

namespaces = {
    'oai': 'http://www.openarchives.org/OAI/2.0/',
    'xsi': "http://www.w3.org/2001/XMLSchema-instance",
    'meta': "http://meresco.org/namespace/harvester/meta",
}

class OaiAddRecord(Transparent):

    @asyncreturn
    def add(self, identifier, partname, lxmlNode):
        record = lxmlNode if iselement(lxmlNode) else lxmlNode.getroot()
        setSpecs = record.xpath('//oai:header/oai:setSpec/text()', namespaces=namespaces)
        sets = set((str(s), str(s)) for s in setSpecs)
        
        namespace = record.nsmap.get(record.prefix or None, '') 
        schemaLocations = record.xpath('@xsi:schemaLocation', namespaces=namespaces)
        ns2xsd = ''.join(schemaLocations).split()
        schema = dict(zip(ns2xsd[::2],ns2xsd[1::2])).get(namespace, '')
        schema, namespace = self._magicSchemaNamespace(record.prefix, partname, schema, namespace)
        metadataFormats=[(partname, schema, namespace)]

        self.do.addOaiRecord(identifier=identifier, sets=sets, metadataFormats=metadataFormats)

    def _magicSchemaNamespace(self, prefix, name, schema, namespace):
        searchForPrefix = prefix or name
        for oldprefix, oldschema, oldnamespace in self.call.getAllMetadataFormats():
            if searchForPrefix == oldprefix:
                return schema or oldschema, namespace or oldnamespace
        return schema, namespace

#TODO: Check if all metadataprefixes exist on adding record to OAI-index.
class OaiAddRecordWithDefaults(Transparent):

    def __init__(self, metadataFormats=None):
        Transparent.__init__(self)
        self._metadataFormats = metadataFormats if metadataFormats else []
        #self._sets = []
        #print 'metadataFormats:', self._metadataFormats 

    def _getPart(self, recordId, partname):
        if self.call.isAvailable(recordId, partname) == (True, True):
            #print 'Getting', partname, ' part for', self._identifier
            stream = self.call.getStream(recordId, partname)
            return parse(stream) #stream.read()
        return None
    
    def _magicSchemaNamespace(self, prefix, name, schema, namespace):
        searchForPrefix = prefix or name
        for oldprefix, oldschema, oldnamespace in self.call.getAllMetadataFormats():
            if searchForPrefix == oldprefix:
                return schema or oldschema, namespace or oldnamespace
        return schema, namespace
    
    @asyncreturn
    def add(self, identifier, **kwargs):
        #record = kwargs['lxmlNode'] if iselement(kwargs['lxmlNode']) else kwargs['lxmlNode'].getroot()
        sets=[]
        fullpath=''
        ## We need meta part for the 'set' definition:
        #record = self._getPart(kwargs.get('identifier'), "meta")
        metapart, headerpart = None, None 
        #print 'Getting meta part for ID:', identifier
        if self.call.isAvailable(identifier, "meta") == (True, True):
            #print 'Getting meta part for ID:', identifier
            stream = self.call.getStream(identifier, "meta")
            metapart = parse(stream)
            
        if self.call.isAvailable(identifier, "header") == (True, True):
            #print 'Getting meta part for ID:', identifier
            stream = self.call.getStream(identifier, "header")
            headerpart = parse(stream)
            #print 'STREAM:', stream.read()
#         e_original.append( deepcopy(lxmlNode).getroot() )
#         e_normalized.append( normalized_part.getroot() )        
        
        #rid = record.xpath('//meta:meta/meta:repository/meta:id/text()', namespaces=namespaces)
        #harvested_set = metapart.xpath('//meta:meta/meta:repository/meta:set/text()', namespaces=namespaces)
        rgid = metapart.xpath('//meta:meta/meta:repository/meta:repositoryGroupId/text()', namespaces=namespaces)
        
        
        setSpecs = headerpart.xpath('//oai:header/oai:setSpec/text()', namespaces=namespaces)
        sets = set(((rgid[0].strip()+':'+str(s)), (rgid[0].strip()+':'+str(s))) for s in setSpecs)
        sets.add((rgid[0].strip(), rgid[0].strip()))
        
        #print 'adding sets:', str(sets)
        #print 'adding metadataFormats:', str(metadataFormats)

        self.do.addOaiRecord(identifier=identifier, sets=sets, metadataFormats=self._metadataFormats)