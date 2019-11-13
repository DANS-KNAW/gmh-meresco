# -*- coding: utf-8 -*-
#WST
import sys
#
sys.path.insert(0, "..")

from seecr.test import SeecrTestCase, CallTrace
from lxml.etree import parse, tostring, XML, fromstring, dump, XMLSchema, parse as lxmlParse
from StringIO import StringIO
from meresco_server.harvestdate import AddHarvestDateToMetaPart
from os.path import abspath, dirname, join
from difflib import unified_diff
from meresco.core import Observable
import time
from weightless.core import be, compose
from unittest import main

metaNS = {'meta' : 'http://meresco.org/namespace/harvester/meta'}

class AddHarvestdateTest(SeecrTestCase):

    def setUp(self):        
        SeecrTestCase.setUp(self)
        self.harvestdate = AddHarvestDateToMetaPart(verbose=False)
        self.observer = CallTrace('observer')
        self.harvestdate.addObserver(self.observer)

    def tearDown(self):
        SeecrTestCase.tearDown(self)
            
    def testAddHarvestDate(self):
    
        self.observer.methods['add'] = lambda *args, **kwargs: (x for x in [])
        
        list( compose(self.harvestdate.all_unknown('add', 'id', 'metadata', 'anotherone', lxmlNode=parse(open("data/anymetapart.xml")), identifier='oai:very:secret:09987' )))
        
        self.assertEquals(1, len(self.observer.calledMethods))
        
        #for m in self.observer.calledMethods:
        #    print 'method name:',m.name, m.args, m.kwargs
            
        result = self.observer.calledMethods[0].kwargs.get('lxmlNode')
        
        self.assertEquals(3, len(self.observer.calledMethods[0].args))
        
        arguments = self.observer.calledMethods[0].args
        
        self.assertEquals("id", arguments[0])
        self.assertEquals("metadata", arguments[1])
        #Zoek harvestDate:
        harvest_date = result.xpath('/meta:meta/meta:record/meta:harvestdate/text()', namespaces=metaNS)
        hdstring = 'to be replaced'
        #print tostring(result)
        if len(harvest_date) > 0: hdstring = harvest_date[0]        
        self.assertTrue( len(harvest_date)==1 and hdstring.startswith( time.strftime("%Y-%m-%dT%H:", time.localtime()) )) 
    
        
    def testKeepExistingHarvestDate(self):
            
        self.observer.methods['add'] = lambda *args, **kwargs: (x for x in [])        
        list( compose(self.harvestdate.all_unknown('add', 'id', 'metadata', 'anotherone', lxmlNode=parse(open("data/anymetapart_harvestdate.xml")), identifier='oai:very:secret:09987' )))
        result = self.observer.calledMethods[0].kwargs.get('lxmlNode')
              
        #Zoek harvestDate:
        harvest_date = result.xpath('/meta:meta/meta:record/meta:harvestdate/text()', namespaces=metaNS)
        #print "HDate:", harvest_date[0]
        self.assertTrue(len(harvest_date)==1)
        self.assertTrue(harvest_date[0] == '2012-02-12T07:50:10Z')
        
if __name__ == '__main__':
    main()