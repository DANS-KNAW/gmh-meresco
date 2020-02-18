#-*- coding: utf-8 -*-
## begin license ##
#
# Copyright (C) 2012-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) Data Archiving and Networked Services (DANS) http://dans.knaw.nl
#
# This file is part of "NARCIS Index"
#
# "NARCIS Index" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "NARCIS Index" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "NARCIS Index"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from lxml.etree import parse, _ElementTree, iselement, tostring, fromstring, XMLSchema, parse as lxmlParse
from lxml import etree

from xml.sax.saxutils import escape as escapeXml

from meresco.core import Transparent
from meresco.xml import xpath
from meresco.xml.namespaces import xpathFirst
from meresco.xml import namespaces


class OaiAddDeleteRecordWithPrefixesAndSetSpecs(Transparent):
    def __init__(self, metadataPrefixes=None, setSpecs=None, name=None):
        Transparent.__init__(self, name=name)
        self._setSpecs = _prepare(setSpecs)
        self._metadataPrefixes = _prepare(metadataPrefixes)

    def add(self, identifier, **kwargs):
        print "OaiAddDeleteRecordWithPrefixesAndSetSpecs:", identifier
        self.call.addOaiRecord(
            identifier=identifier,
            setSpecs=self._setSpecs(identifier=identifier, **kwargs),
            metadataPrefixes=self._metadataPrefixes(identifier=identifier, **kwargs))
        return
        yield

    def delete(self, identifier, **kwargs):
        self.call.deleteOaiRecord(
            identifier=identifier,
            setSpecs=self._setSpecs(identifier=identifier, **kwargs),
            metadataPrefixes=self._metadataPrefixes(identifier=identifier, **kwargs))
        return
        yield

def _prepare(iterableOrCallable):
    if iterableOrCallable is None:
        return lambda **kwargs: []
    return iterableOrCallable if callable(iterableOrCallable) else lambda **kwargs: iterableOrCallable


class OaiAddRecord(Transparent):

    def __init__(self, metadataPrefixes=None, name=None):
        Transparent.__init__(self, name=name)
        self._metadataPrefixes = metadataPrefixes if metadataPrefixes else []

    def add(self, identifier, partname, lxmlNode):

        # origineel record en normdoc komt binnen vanaf de gateway:
        # - origineel oai header (setSpecs)
        # - meta part (repositoryGroupId)

        lxml_record_part = fromstring(lxmlNode.xpath('//document:document/document:part[@name="record"]/text()', namespaces=namespaces)[0])
        lxml_meta_part = fromstring(lxmlNode.xpath('//document:document/document:part[@name="meta"]/text()', namespaces=namespaces)[0])

        oaiHeader = xpathFirst(lxml_record_part, '//oai:header')
        repogroupid = xpathFirst(lxml_meta_part, '//meta:repository/meta:repositoryGroupId/text()')

        setSpecs = oaiHeader.xpath('//oai:setSpec/text()', namespaces=namespaces)
        sets = set(((repogroupid.strip()+':'+str(s)), "set " + (repogroupid.strip()+':'+str(s))) for s in setSpecs)
        sets.add((repogroupid.strip(), "set " + repogroupid.strip()))
        
        self.call.addOaiRecord(identifier=identifier, sets=sets, metadataFormats=self._metadataPrefixes)
        return
        yield

    def _magicSchemaNamespace(self, prefix, name, schema, namespace):
        searchForPrefix = prefix or name
        for oldprefix, oldschema, oldnamespace in self.call.getAllMetadataFormats():
            if searchForPrefix == oldprefix:
                return schema or oldschema, namespace or oldnamespace
        return schema, namespace


# class OaiAddRecord(Transparent):
#     def add(self, identifier, partname, lxmlNode):
#         record = lxmlNode if iselement(lxmlNode) else lxmlNode.getroot()
#         oaiHeader = xpathFirst(record, 'oai:header')
#         if oaiHeader is None:
#             oaiHeader = xpathFirst(record, '/oai:header')

#         setSpecs = [] if oaiHeader is None else xpath(oaiHeader, 'oai:setSpec/text()')
#         sets = set((str(s), str(s)) for s in setSpecs)

#         namespace = record.nsmap.get(record.prefix or None, '')
#         schemaLocation = record.attrib.get(expandNs('xsi:schemaLocation'), '')
#         ns2xsd = schemaLocation.split()
#         schema = dict(zip(ns2xsd[::2],ns2xsd[1::2])).get(namespace, '')
#         schema, namespace = self._magicSchemaNamespace(record.prefix, partname, schema, namespace)
#         metadataFormats=[(partname, schema, namespace)]
#         self.call.addOaiRecord(identifier=identifier, sets=sets, metadataFormats=metadataFormats)
#         return
#         yield

#     def _magicSchemaNamespace(self, prefix, name, schema, namespace):
#         searchForPrefix = prefix or name
#         for oldprefix, oldschema, oldnamespace in self.call.getAllMetadataFormats():
#             if searchForPrefix == oldprefix:
#                 return schema or oldschema, namespace or oldnamespace
#         return schema, namespace