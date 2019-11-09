## begin license ##
#
#    Meresco Examples is a project demonstrating some of the features of
#    various Meresco components.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
#
#    This file is part of Meresco Examples.
#
#    Meresco Examples is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Examples is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Examples; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from sys import stdout

from os.path import join, isdir
from os import makedirs

from meresco.core import TransactionScope, ResourceManager
from meresco.core.observable import Observable

from weightless.core import Transparent, be, compose
from meresco.components import StorageComponent, FilterField, RenameField, XmlParseLxml, XmlXPath, XmlPrintLxml, Xml2Fields, Venturi, FilterMessages, Amara2Lxml, RewritePartname, Lxml2Amara #, Rss, RssItem

from meresco.components.http import PathFilter, ObservableHttpServer
from meresco.components.sru import SruParser, SruHandler, SRURecordUpdate
from meresco.oai import OaiJazz #, OaiProvenance #OaiAddRecordWithDefaults, OaiAddRecord, OaiPmh
from oaiaddrecord_gh import OaiAddRecordWithDefaults#, OaiAddRecord
from weightless.io import Reactor

# 'Overridden' from meresco.components package:
from meresco_components.oaiprovenance import OaiProvenance
from meresco_components.oaipmh import OaiPmh

#DEBUG
#from tools.dnadebugger import DNADebug

from normalize_nl_didl import Normalize_nl_DIDL
from normalize_nl_mods import Normalize_nl_MODS

from nl_didl_combined import NL_DIDL_combined
from meresco.components import FilterPartByName

#We'll use MD5-hash to divide records into multiple folders.
from storagesplit import Md5HashDistributeStrategy
from meresco.components.storagecomponent import HashDistributeStrategy, DefaultStrategy

#Logging:
from logger import Logger

#RSS:
from logger_rss import LoggerRSS

#XML validator:
from xml_validator import Validate

# Add current harvestdate:
from harvestdate import AddHarvestDateToMetaPart

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

NL_DIDL_NORMALISED_PREFIX = 'nl_didl_norm'
NL_DIDL_COMBINED_PREFIX = 'nl_didl_combined'

def createUploadHelix(storageComponent, oaiJazz, loggerComponent):

    return \
        (TransactionScope('batch'),
            (TransactionScope('record'),
                (Venturi(
                    should=[ # Order DOES matter: First part goes first!
                        {'partname':'header', 'xpath':'/document:document/document:part[@name="header"]/text()', 'asString':False},                        
                        {'partname':'meta', 'xpath':'/document:document/document:part[@name="meta"]/text()', 'asString':False},
                        {'partname':'metadata', 'xpath':'/document:document/document:part[@name="metadata"]/text()', 'asString':False}
                    ],
                    namespaceMap=namespacesMap),
                    # Remove all delete msgs from storage and OAI:
                    (FilterMessages(allowed=['delete']),
                        #(DNADebug(enabled=False, prefix='DELETE'),
                            (storageComponent,),
                            (oaiJazz,)
                        #)
                    ),
                    (FilterMessages(allowed=['add']),
                    
                        ## Write harvestdate (=now()) to meta part (OAI provenance)
                        (FilterPartByName(included=['meta']),                            
                            (AddHarvestDateToMetaPart(verbose=False),)                            
                        ),                    
                        # Store ALL (original)parts retrieved by Venturi (required ('should') and optional ('could') parts).
                        # Write all uploadParts to storage (header, meta & metadata)
                        (XmlPrintLxml(fromKwarg='lxmlNode', toKwarg='data'),
                                (storageComponent,)
                        ),
                        (FilterPartByName(included=['metadata']), # Normalize 'metadata' part:
                            #(DNADebug(enabled=False, prefix='add metadata'),
                                # Validate DIDL and MODS part against their xsd-schema:
                                (Validate([('DIDL container','//didl:DIDL', 'didl.xsd'), ('MODS metadata', '//mods:mods', 'mods-3-6.xsd')], nsMap=namespacesMap), 
                                    (Normalize_nl_DIDL(nsMap=namespacesMap), # Normalize DIDL in metadataPart
                                        (loggerComponent,),
                                        (Normalize_nl_MODS(nsMap=namespacesMap), # Normalize MODS in metadataPart.
                                            (loggerComponent,),
                                            (XmlPrintLxml(fromKwarg='lxmlNode', toKwarg='data'), # Convert it from etree.ElementTree to plaintext
                                                (RewritePartname(NL_DIDL_NORMALISED_PREFIX), # Rename normalized partName from 'metadata' to 'nl_didl_norm'
                                                    #(DNADebug(enabled=False, prefix='to storage'),
                                                        (storageComponent,) # Write normalized partName to storage                                    
                                                    #)
                                                )
                                            ),
                                            # Create and store Combined format:
                                            (NL_DIDL_combined(nsMap=namespacesMap), # Create combined format from stored metadataPart and normalized part. 
                                                (XmlPrintLxml(fromKwarg='lxmlNode', toKwarg='data'), # Convert it to plaintext
                                                    (RewritePartname(NL_DIDL_COMBINED_PREFIX), # Rename combined partName
                                                         (storageComponent,) # Write combined partName to storage
                                                    )
                                                )
                                            ),
                                            # Add parts to OAI repository/index
                                            #(DNADebug(enabled=False, prefix='ADD2OAI'),
                                                (OaiAddRecordWithDefaults(metadataFormats=[('metadata', 'http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/did/didmodel.xsd', 'urn:mpeg:mpeg21:2002:02-DIDL-NS'),
                                                                                           (NL_DIDL_NORMALISED_PREFIX, '', 'http://gh.kb-dans.nl/normalised/v0.9/'),
                                                                                           (NL_DIDL_COMBINED_PREFIX, '', 'http://gh.kb-dans.nl/combined/v0.9/')]),
                                                    (storageComponent,), 
                                                    (oaiJazz,) # Assert partNames header and meta are available from storage!
                                                ) #! OaiAddRecord
                                            #) #!Debug
                                        )
                                    )
                                )
                            #) #Debug
                        ) #!FilterPartNames(allowed=['metadata']
                    ) # !FilterMessages(allowed=['add']
                ) # !venturi
            ) # !record
        ) # !batch

def dna(reactor, host, portNumber, databasePath):
    #Choose ONE storage strategy:
    #strategie = HashDistributeStrategy() #irreversible?
    #strategie = DefaultStrategy()
    strategie = Md5HashDistributeStrategy()
    
    ## Define which parts should be removed from storage on an SRU delete update.
    storageComponent = StorageComponent(join(databasePath, 'storage'), partsRemovedOnDelete=[NL_DIDL_NORMALISED_PREFIX, NL_DIDL_COMBINED_PREFIX, 'metadata'], strategy=strategie)

    loggerComponent = Logger(join(databasePath, 'logger'))
    
    oaiJazz = OaiJazz(join(databasePath, 'oai', 'data'))

    
    return \
        (Observable(),
            (ObservableHttpServer(reactor, portNumber),
                (PathFilter("/update"),
                    (SRURecordUpdate(),
                        (Amara2Lxml(fromKwarg='amaraNode', toKwarg='lxmlNode'),
                            createUploadHelix(storageComponent, oaiJazz, loggerComponent)
                        )
                    )
                ),
                (PathFilter('/oai'), #XWAIT: (OaiPmh(repositoryName='repositoryName', adminEmail='adminEmail', batchSize=2, supportXWait=True)
                    (OaiPmh(repositoryName='Gemeenschappelijke Harvester DANS-KB', adminEmail='harvester@dans.knaw.nl', batchSize=100, fixIdentifyBaseURL=True), ## batchSize = number of records before issueing a resumptionToken...
                        (oaiJazz,),
                        (storageComponent,),
                        (OaiProvenance( ## NOTE: If one of the following fields lacks, provenance will NOT be written.
                                nsMap=namespacesMap,                                                          
                                baseURL = ('meta', '//*[local-name() = "baseurl"]/text()'),
                                harvestDate = ('meta', '//*[local-name() = "harvestdate"]/text()'),                                                                


                                #See: http://www.openarchives.org/OAI/2.0/guidelines-provenance.htm
                                metadataNamespace = (NL_DIDL_NORMALISED_PREFIX, '//mods:mods/namespace::node()[name()="" or name()="mods" or contains(.,"mods")]'),                                
                                # Some 'magic' here: xpath() function may return different types.
                                # (Namespace) nodes return tuple's instead of an Element Object. (string) Functions return strings, etc...
                                # Since meresco.oai.OaiProvenance handles all return objects from xpath() the same, the results were unpredictable.
                                # This is why we have overriden the XmlCompose.
                                # See: http://lxml.de/xpathxslt.html#xpath-return-values
                                                                
                                identifier = ('header', '/oai:header/oai:identifier/text()'),                                
                                datestamp = ('header', '/oai:header/oai:datestamp/text()')
                            ),
                            (storageComponent,)
                        )
                    )
                ),             
                (PathFilter('/rss'),
                    (LoggerRSS( title = 'Gemeenschappelijke Harvester DANS-KB', description = 'Harvester normalisation log for: ', link = 'http://rss.gharvester.dans.knaw.nl/rss', maximumRecords = 30),
                        (loggerComponent,
                                (storageComponent,)                            
                        )
                    )
                )
            )
        )


config = {
    'host': 'localhost',
    'port': 8000
}

if __name__ == '__main__':
    databasePath = '/data/meresco/gharvester'
    if not isdir(databasePath):
        makedirs(databasePath)

    reactor = Reactor()
    server = be(dna(reactor, config['host'], config['port'], databasePath))
    ## server.once.observer_init() # OUD: alle generators dienen nu tezamen gepakt te worden:
    list(compose(server.once.observer_init()))

    print "Server listening on", config['host'], "at port", config['port']
    print "   - database:", databasePath, "\n"
    stdout.flush()
    reactor.loop()