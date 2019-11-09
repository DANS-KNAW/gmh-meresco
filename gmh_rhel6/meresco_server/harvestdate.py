# -*- coding: utf-8 -*-
from meresco.core import Observable
from lxml.etree import parse, _ElementTree, tostring
#from lxml.etree import parse, tostring, XML, fromstring, dump, XMLSchema, parse as lxmlParse
from StringIO import StringIO
from lxml import etree
import time

HVSTR_NS = '{http://meresco.org/namespace/harvester/meta}'

class AddHarvestDateToMetaPart(Observable):
    
    def __init__(self, verbose=False):
        Observable.__init__(self)
        self._verbose = verbose

    def _detectAndConvert(self, anObject):
        if type(anObject) == _ElementTree:
            return self._convertMetaPart(anObject)
        return anObject

    def all_unknown(self, method, *args, **kwargs):        
        # Create our new args to send:
        newArgs = [self._detectAndConvert(arg) for arg in args]
        newKwargs = dict((key, self._detectAndConvert(value)) for key, value in kwargs.items()) 
        yield self.all.unknown(method, *newArgs, **newKwargs)

    def _convertMetaPart(self, lxmlNode):
        e_root = lxmlNode.getroot()
        _bln_has_harvestdate = False
        # TODO: use .find() instead of iterating over all elements?
        #Check if tag is already available, we dont want it twice, or overwritten when re-indexing f.e:
        for child in e_root.iterchildren():
            if child.tag == HVSTR_NS + 'record':
                for recordkind in child.iterchildren():
                    if recordkind.tag == HVSTR_NS + 'harvestdate':
                        _bln_has_harvestdate = True
                        if self._verbose: print 'Harvestdate tag already available from meta part:' , recordkind.text , '. Skipping adding harvestdate...'
                if not _bln_has_harvestdate:
                    e_harvestdate = etree.SubElement(child, HVSTR_NS + 'harvestdate')
                    e_harvestdate.text = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime())
                    if self._verbose: print 'Added harvestdate tag to meta part:', e_harvestdate.text
                break
        return lxmlNode