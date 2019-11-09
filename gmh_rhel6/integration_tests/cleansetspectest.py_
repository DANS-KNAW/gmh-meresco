# -*- coding: utf-8 -*-

from cq2utils import CQ2TestCase, CallTrace

from lxml.etree import parse, tostring, XML, fromstring
from StringIO import StringIO
from narcis.cleansetspecs import CleanSetSpecs
from meresco.framework import Observable

HEADER = """<header xmlns="http://www.openarchives.org/OAI/2.0/">
	<identifier>oai:depot.knaw.nl:565</identifier>
	<datestamp>2009-02-13T16:15:44Z</datestamp>
	<setSpec>74797065733D61727469636C65</setSpec>
	<setSpec>66756C6C746578743D7075626C6963</setSpec>
	<setSpec>696E73746974757465733D4D65657274656E73</setSpec></header>"""
	
HEADERRESULT = """<header xmlns="http://www.openarchives.org/OAI/2.0/"><identifier>oai:depot.knaw.nl:565</identifier><datestamp>2009-02-13T16:15:44Z</datestamp></header>"""

# act, prs & ond worden niet meer in dit component gefilterd...
#setSpecs = ['66756C6C746578743D7075626C6963', 'personen', 'organisaties', 'activiteiten', 'activiteit']
#expectedResults = [setSpecs[0], 0, 0, 0, 1]
#headers = [HEADER % (arg) for arg in setSpecs]

class CleanSetSpecTest(CQ2TestCase):

	def testCleanSetSpec(self):
		setSpec = CleanSetSpecs()
		result = setSpec.convert(parse(StringIO(HEADER)))
		self.assertEquals(HEADERRESULT, tostring(result))
		#result = setSpec.convert(parse(StringIO("<blah></blah>")))
		#print tostring(result)