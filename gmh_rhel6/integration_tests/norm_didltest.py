# -*- coding: utf-8 -*-

from seecr.test import SeecrTestCase, CallTrace
from lxml.etree import parse, tostring, XML, fromstring, dump, XMLSchema, parse as lxmlParse
from StringIO import StringIO
from meresco_server.normalize_nl_didl import Normalize_nl_DIDL
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


class NormDIDLTest(SeecrTestCase):

    def setUp(self):
    
        SeecrTestCase.setUp(self)

        self.schemasPath = join(dirname(abspath(__file__)), '../meresco_server/xsd')
        self.norm_didl = Normalize_nl_DIDL(nsMap=namespacesMap)
        self.observer = CallTrace('observer')
        self.norm_didl.addObserver(self.observer)
        

    def testOne(self):
        self.observer.methods['add'] = lambda *args, **kwargs: (x for x in [])
        list( compose(self.norm_didl.all_unknown('add', 'id', 'metadata', 'anotherone', lxmlNode=parse(open("data/didl_mods.xml")), identifier='oai:very:secret:09987' )))        
        self.assertEquals(4, len(self.observer.calledMethods))
        
        #for m in self.observer.calledMethods:
        #    print 'method name:',m.name, m.args, m.kwargs
        result = self.observer.calledMethods[3].kwargs.get('lxmlNode')
                
        self.assertEquals(2, len(self.observer.calledMethods[0].args))
        
        arguments = self.observer.calledMethods[1].args
        
        self.assertEquals("oai:very:secret:09987", arguments[0])
        #Test logMessage:
        self.assertEquals("Found objectFile in depricated dip:ObjectType. This should have been: rdf:type/@rdf:resource", arguments[1])
        
        
        #Get DIDL from record:
        didl = result.xpath("//didl:DIDL", namespaces=namespacesMap)
        
        # Should be exactly 1:
        self.assertTrue(len(didl)==1)
        
        #print tostring(didl[0], pretty_print = True, encoding='utf-8')        
        
        #Validate against schema:
        didlSchema = XMLSchema(lxmlParse(open(join(self.schemasPath, 'didl.xsd'))))                
        didlSchema.validate(didl[0])
        if didlSchema.error_log.last_error:
            self.fail(didlSchema.error_log.last_error)        
        
        # Check if expected result:        
        expectedResult = open("data/didl_converted.xml").read()
        # print "EXPECTED DIDL:", tostring(didl[0], pretty_print = True, encoding='utf-8')       
        self.assertEqualsWithDiff(expectedResult, tostring(didl[0], pretty_print = True, encoding='utf-8'))


    def tearDown(self):
        SeecrTestCase.tearDown(self)       
        
        
    def assertEqualsWithDiff(self, expected, result):
        diffs = list(unified_diff([x.strip() for x in result.split('\n') if x.strip()], [x.strip() for x in expected.split('\n') if x.strip()], fromfile='result', tofile='expected', lineterm=''))
        self.assertFalse(diffs, '\n' + '\n'.join(diffs))
        