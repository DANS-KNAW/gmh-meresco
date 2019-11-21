## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
# 
# This file is part of "Meresco Components"
# 
# "Meresco Components" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "Meresco Components" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "Meresco Components"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

from lxml.etree import parse, XMLSchema, XMLSchemaParseError, _ElementTree, tostring
from StringIO import StringIO

from weightless.core import NoneOfTheObserversRespond, DeclineMessage
from meresco.core import Observable
from meresco.components import lxmltostring
from meresco.components.xml_generic import  __file__ as xml_genericpath
from meresco.components.xml_generic.validate import ValidateException

## Schema validatie:
from os.path import abspath, dirname, join

oftenUsedNamespaces = {
    'oai_dc': "http://www.openarchives.org/OAI/2.0/oai_dc/",
    'dc': "http://purl.org/dc/elements/1.1/",
    'oai': "http://www.openarchives.org/OAI/2.0/",
    'lom': "http://ltsc.ieee.org/xsd/LOM",
    'meta': "http://meresco.org/namespace/harvester/meta",
}

class Validate(Observable):

    def __init__(self, xSDPathList=[], nsMap=None):
        Observable.__init__(self)
        
        self._namespacesMap = oftenUsedNamespaces.copy()
        self._namespacesMap.update(nsMap or {})
        self._xmlSchemas = []
        
        ## Fill the schemas list for later use:
        for strName, strXPath, schemaPath in xSDPathList:
            print 'schema init:', strName, strXPath, schemaPath
            try:
                self._xmlSchemas.append((strName, strXPath, XMLSchema(parse(join(join(dirname(abspath(__file__)), 'xsd'), schemaPath) ) ) ))
            except XMLSchemaParseError, e:
                print 'XMLSchemaParseError.............',e.error_log.last_error
                raise


    def all_unknown(self, message, *args, **kwargs):
        self._detectAndValidate(*args, **kwargs)
        yield self.all.unknown(message, *args, **kwargs)

    def do_unknown(self, message, *args, **kwargs):
        self._detectAndValidate(*args, **kwargs)
        return self.do.unknown(message, *args, **kwargs)

    def any_unknown(self, message, *args, **kwargs):
        self._detectAndValidate(*args, **kwargs)
        try:
            response = yield self.any.unknown(message, *args, **kwargs)
            raise StopIteration(response)
        except NoneOfTheObserversRespond:
            raise DeclineMessage

    def call_unknown(self, message, *args, **kwargs):
        self._detectAndValidate(*args, **kwargs)
        try:
            return self.call.unknown(message, *args, **kwargs)
        except NoneOfTheObserversRespond:
            raise DeclineMessage

    def _detectAndValidate(self, *args, **kwargs):
        allArguments = list(args) + kwargs.values()
        for arg in allArguments:
            if type(arg) == _ElementTree: #Should be only one...
                
                for strName, strXPath, schema in self._xmlSchemas:
                    ## Doe xpath op betreffende XML/argument:
                    xml = arg.xpath(strXPath, namespaces=self._namespacesMap)        
                    if len(xml) > 0:
                        schema.validate(xml[0])                
                        if schema.error_log:
                            exception = ValidateException(formatXSDException(strName + " is NOT valid.", None, schema)) #, arg                     
                            self.do.logException(exception)
                            raise exception
                    else:
                        exception = ValidateException(formatExceptionLine("Mandatory " + strName + " NOT found."))                    
                        self.do.logException(exception)
                        raise exception

def assertValid(xmlString, schemaPath):
    schema = XMLSchema(parse(open(schemaPath)))
    toValidate = parse(StringIO(xmlString))
    schema.validate(toValidate)
    if schema.error_log:
        raise AssertionError(formatException("assertValid", schema, toValidate))

def formatXSDException(strMsg, identifier, schema): #, lxmlNode
    message = formatExceptionLine(strMsg, identifier) + "\n"
    message += str(schema.error_log.last_error) + "\n\n"
    #for nr, line in enumerate(lxmltostring(lxmlNode, pretty_print=True).split('\n')):
    #   message += "%s %s\n" % (nr+1, line)
    return message
    
def formatExceptionLine(strMsg, identifier=None, prefix=None):
    str_mssg = prefix +" "+ strMsg if prefix is not None else strMsg
    return str_mssg if identifier is None else identifier + " <=> " + str_mssg