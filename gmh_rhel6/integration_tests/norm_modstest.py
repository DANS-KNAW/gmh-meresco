# -*- coding: utf-8 -*-

from seecr.test import SeecrTestCase, CallTrace
from lxml.etree import parse, tostring, XML, fromstring, dump, XMLSchema, parse as lxmlParse
from StringIO import StringIO
from meresco_server.normalize_nl_mods import Normalize_nl_MODS
from weightless.core import be, compose
from os.path import abspath, dirname, join
from difflib import unified_diff
from meresco.core import Observable



namespacesMap = {
    'dip'     : 'urn:mpeg:mpeg21:2005:01-DIP-NS',
    'dii'     : 'urn:mpeg:mpeg21:2002:01-DII-NS',
    'document': 'http://meresco.org/namespace/harvester/document',
    'oai'     : 'http://www.openarchives.org/OAI/2.0/',
    'meta'    : 'http://meresco.org/namespace/harvester/meta',
    'oai_dc'  : 'http://www.openarchives.org/OAI/2.0/oai_dc/',
    'dc'      : 'http://purl.org/dc/elements/1.1/',
    'mods'    : 'http://www.loc.gov/mods/v3',
    'didl'    : 'urn:mpeg:mpeg21:2002:02-DIDL-NS',
    'rdf'     : 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'ucp'     : 'info:lc/xmlns/update-v1',
    'dcterms' : 'http://purl.org/dc/terms/',
    'xsi' : 'http://www.w3.org/2001/XMLSchema-instance'
}


class NormModsTest(SeecrTestCase):

    def setUp(self):
    
        SeecrTestCase.setUp(self)

        self.schemasPath = join(dirname(abspath(__file__)), '../meresco_server/xsd')
        self.norm_mods = Normalize_nl_MODS(nsMap=namespacesMap)
        self.observer = CallTrace('observer')
        self.norm_mods.addObserver(self.observer)
        

    def testOne(self):
        self.observer.methods['add'] = lambda *args, **kwargs: (x for x in [])
        list( compose(self.norm_mods.all_unknown('add', 'id', 'metadata', 'anotherone', lxmlNode=parse(open("data/didl_mods.xml")), identifier='oai:very:secret:09987' )))        
        self.assertEquals(3, len(self.observer.calledMethods))
        
        # for m in self.observer.calledMethods:
        #    print 'method name:',m.name, m.args, m.kwargs
        result = self.observer.calledMethods[2].kwargs.get('lxmlNode')
        
        # print "Converted:", tostring(result)
        self.assertEquals(2, len(self.observer.calledMethods[0].args))
        
        arguments = self.observer.calledMethods[2].args
        self.assertEquals("id", arguments[0])
        self.assertEquals("metadata", arguments[1])
        
        #Get MODS from record:
        mods = result.xpath("//mods:mods", namespaces=namespacesMap)
        
        # Should be exactly 1:
        self.assertTrue(len(mods)==1)
        
        #print tostring(mods[0], pretty_print = True, encoding='utf-8')        
        
        #Validate against schema:
        modsSchema = XMLSchema(lxmlParse(open(join(self.schemasPath, 'mods-3-6.xsd'))))                
        modsSchema.validate(mods[0])
        if modsSchema.error_log.last_error:
            self.fail(modsSchema.error_log.last_error)        
        
        # Check if expected result:        
        expectedResult = open("data/mods_converted.xml").read()
        # print "EXPECTED MODS:", tostring(mods[0], pretty_print = True, encoding='utf-8')      
        self.assertEqualsWithDiff(expectedResult, tostring(mods[0], pretty_print = True, encoding='utf-8'))


    def tearDown(self):
        SeecrTestCase.tearDown(self)       
        
        
    def assertEqualsWithDiff(self, expected, result):
        diffs = list(unified_diff([x.strip() for x in result.split('\n') if x.strip()], [x.strip() for x in expected.split('\n') if x.strip()], fromfile='result', tofile='expected', lineterm=''))
        self.assertFalse(diffs, '\n' + '\n'.join(diffs))
        