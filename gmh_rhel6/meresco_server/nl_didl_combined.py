# -*- coding: utf-8 -*-
from lxml.etree import parse, _ElementTree, tostring
from lxml import etree
from meresco.core import Observable
from copy import deepcopy
from StringIO import StringIO
from weightless.core import Transparent, be, compose

#TODO: lxml staat het gebruik van conolisednames niet meer toe: gebruik kwarg: prefix="[ns_alias]"
# This component handles ADD messages only.
# It will try to convert the data from the 'metadata' part into GH combined format.
# If it fails in doing so, it will block (NOT pass) the ADD message.
# Returns: xml-string.
            
GH_COMBINED_NS = "http://gh.kb-dans.nl/combined/v0.9/"
GH_COMBINED = "{%s}" % GH_COMBINED_NS
NSMAP = {None : GH_COMBINED_NS} # Default namespace (no prefix)

class NL_DIDL_combined(Observable):

    def __init__(self, nsMap={}):
        Observable.__init__(self)
        self._nsMap=nsMap
        self._bln_success = False
        
    def _detectAndConvert(self, anObject):
        if type(anObject) == _ElementTree:
            return self.convert(anObject)
        return anObject

    def convert(self, lxmlNode):
        self._bln_success = False
        result_tree = self._combineRecord(lxmlNode)
        if result_tree != None:
            self._bln_success = True
        return result_tree

    def all_unknown(self, method, *args, **kwargs):
        self._identifier = kwargs.get('identifier')
        newArgs = [self._detectAndConvert(arg) for arg in args]     
        newKwargs = dict((key, self._detectAndConvert(value)) for key, value in kwargs.items())
        if self._bln_success:
            return self.all.unknown(method, *newArgs, **newKwargs)

    def _combineRecord(self, lxmlNode):
        #Get partName from disk to combine:
        storage_part = self._getPart(self._identifier, "metadata")
        
        #Create wrapper:
        root = etree.Element(GH_COMBINED + "nl_didl_combined", nsmap=NSMAP)
        e_original = etree.SubElement(root, GH_COMBINED + "nl_didl")
        e_normalized = etree.SubElement(root, GH_COMBINED + "nl_didl_norm")        
        
        orginal_didl = storage_part.xpath('//didl:DIDL', namespaces=self._nsMap)
        #print(etree.tostring(didl_xml[0], pretty_print=True))
        if orginal_didl:
            e_original.append( orginal_didl[0] )
        e_normalized.append( lxmlNode.getroot() )        
        
        return root
        
    def _getPart(self, recordId, partname):
        if self.call.isAvailable(recordId, partname) == (True, True):
            #print 'Getting', partname, ' part for', self._identifier
            stream = self.call.getStream(recordId, partname)
            return parse(stream) #stream.read()
        return None
            
    def __str__(self):
        return 'NL_DIDL_combined'
