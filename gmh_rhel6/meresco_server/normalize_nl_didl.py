# -*- coding: utf-8 -*-
from lxml.etree import parse, _ElementTree, tostring, XMLSchema, parse as lxmlParse
from lxml import etree
from xml.sax.saxutils import escape as escapeXml
from meresco.core import Observable
from copy import deepcopy
from StringIO import StringIO
from meresco.components.xml_generic.validate import ValidateException
from xml_validator import formatExceptionLine
from dateutil.parser import parse as parseDate

import commons as comm

#Schema validatie:
from os.path import abspath, dirname, join

# This component handles ADD messages only.
# It will try to convert the supplied data (KNAWLong) from the 'metadata' part into KNAWshort. All other parts and data formats are ignored (blocked).
# If it fails in doing so, it will block (NOT pass) the ADD message.
# Returns: xml-string!

## Default xml-encoding:
XML_ENCODING = 'utf-8'
STR_DIDL = "DIDL:"

LOGGER1 = "Top level Item date modified replaced by more recent child Item date modified."
LOGGER2 = "Invalid mimeType found : "
LOGGER3 = "Found descriptiveMetadata in rdf:type/@resource. This should have been: rdf:type/@rdf:resource"
LOGGER4 = "Found descriptiveMetadata in depricated dip:ObjectType. This should have been: rdf:type/@rdf:resource"
LOGGER5 = "Invalid dcterms:modified: "
LOGGER6 = "Found objectFile in rdf:type/@resource. This should have been: rdf:type/@rdf:resource"
LOGGER7 = "Found objectFile in depricated dip:ObjectType. This should have been: rdf:type/@rdf:resource"
LOGGER8 = "Invalid mimeType found for objectfile Resource: "
LOGGER9 = "HumanStartPage descriptor found in resource attribute not in rdf namespace."
LOGGER10 = "HumanStartPage descriptor found in depricated dip namespace."
LOGGER11 = "No HumanStartPage found."
LOGGER12 = "Invalid mimeType found for humanstartpage Resource: "
LOGGER13 = "No mimeType found for humanstartpage."

EXCEPTION0 = "Invalid format for mandatory persistent identifier (urn:nbn) in top level Item: "
EXCEPTION1 = "Mandatory persistent identifier (urn:nbn) in top level DIDL Item not found."
EXCEPTION2 = "Mandatory dateModified in top level DIDL Item not a valid ISO8601 date: "
EXCEPTION3 = "Mandatory dcterms:modified in top level DIDL Item not found."
EXCEPTION4 = "Mandatory Resource location (the url for the urn:nbn persistent identifier) in top level DIDL Item not found."
EXCEPTION5 = "Mandatory Resource location (the url for the urn:nbn persistent identifier) in top level DIDL Item is not a valid url: "
EXCEPTION6 = "Mandatory MODS in descriptiveMetadata element not found in DIDL record."
EXCEPTION7 = "Mandatory descriptiveMetadata item element not found."
EXCEPTION8 = "No accessRights found for objectfile."
EXCEPTION9 = "Mandatory resource location for objectfile is not a valid URL: "
EXCEPTION10 = "Mandatory Resource not found in DIDL objectFile Item."
EXCEPTION11 = "Mandatory Resource URL not found in humanstartpage Item."
EXCEPTION12 = " is an invalid accessRights term for an objectfile. Use: Open, Closed or RestrictedAccess."


## Translation maps (key needs to be found somewhere in textvalues to be mapped):
## Taken from EduStandaard Semantiek:
pubVersions = {
    'publishedversion':'info:eu-repo/semantics/publishedVersion',
    'updatedversion'  :'info:eu-repo/semantics/updatedVersion',
    'acceptedversion'  :'info:eu-repo/semantics/acceptedVersion',
    'submittedversion'  :'info:eu-repo/semantics/submittedVersion',
    'draft'  :'info:eu-repo/semantics/draft'
}

accessRights = {
    'openaccess':'http://purl.org/eprint/accessRights/OpenAccess',
    'restrictedaccess'  :'http://purl.org/eprint/accessRights/RestrictedAccess',
    'closedaccess': 'http://purl.org/eprint/accessRights/ClosedAccess',
}

## Default DIDL Descriptor template: 
descr_templ = """<didl:Descriptor>
                    <didl:Statement mimeType="application/xml">
                        %s
                    </didl:Statement>
                </didl:Descriptor>"""  


class Normalize_nl_DIDL(Observable):
    """A class that normalizes DIDL container to the Edustandaard applicationprofile"""
    
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

        ## Remove all XML-comments from the (normalized) DIDL/MODS tree. Cannot supply parser options to Venturi: XML-Comments will also be read by iterchildren().
        comments = lxmlNode.xpath('//comment()')    
        for c in comments:
            p = c.getparent()
            p.remove(c)

        result_tree = self._normalizeRecord(lxmlNode)
        if result_tree != None:
            self._bln_success = True            
        return result_tree

    def all_unknown(self, method, *args, **kwargs):
        self._identifier = kwargs.get('identifier')
        newArgs = [self._detectAndConvert(arg) for arg in args]     
        newKwargs = dict((key, self._detectAndConvert(value)) for key, value in kwargs.items())
        if self._bln_success:
            yield self.all.unknown(method, *newArgs, **newKwargs)

    def _normalizeRecord(self, lxmlNode):
        str_didl = ''
        
        ## Call our functions:
        didlFunctions = [ self._getRootElement, self._getTopItem, self._getDescriptiveMetadata, self._getObjectfiles, self._getHumanStartPage ]     
        for function in didlFunctions:
            str_didl += function(lxmlNode)
        
        ## Close DIDL:
        str_didl += "</didl:Item></didl:DIDL>"
                
        ## Define our parser:
        parser = etree.XMLParser(remove_blank_text=True, ns_clean=True)
        
        try:
            e_didl = parse(StringIO(str_didl), parser)
            item_to_focus = e_didl.xpath('//didl:Item/didl:Item', namespaces=self._nsMap)
          
            for item in item_to_focus:
                resource_to_focus = item.xpath('self::didl:Item/didl:Component/didl:Resource', namespaces=self._nsMap)
                
                if len(resource_to_focus) > 1:
                    new_resource_to_focus = deepcopy(resource_to_focus)
                    comp = resource_to_focus[0].getparent()  #<component>
                    item.remove(comp) ## Item without component tag
                    parent_item = item.getparent()
                    
                    for r in resource_to_focus:
                        comp.remove(r) ## Remove all children from the component tag

                    for nr in new_resource_to_focus:
                        new_comp = deepcopy(comp) #copy the original(empty) component tag
                        new_comp.append(nr) #add the Resource tag to the empty copied component tag
                        new_item = deepcopy(item) #copy the original item tag
                        new_item.append(new_comp) # add to the copied item
                        parent_item.append(new_item) #add the copied item to the parent

                    parent_item.remove(item)
            
            etree.cleanup_namespaces(e_didl)

            #root = etree.Element('temp', nsmap=self._nsMap)
            #root.append(e_didl)
            #etree.cleanup_namespaces(root)            
            #return root.find( ('{%s}DIDL') % self._nsMap['didl']
            
            return e_didl
        except:
            print 'Error while parsing: ', str_didl
            raise
        
        
    def _getRootElement(self, lxmlNode):

        return """<didl:DIDL 
    xmlns:didl="urn:mpeg:mpeg21:2002:02-DIDL-NS" 
    xmlns:dii="urn:mpeg:mpeg21:2002:01-DII-NS" 
    xmlns:dc="http://purl.org/dc/elements/1.1/" 
    xmlns:dcterms="http://purl.org/dc/terms/" 
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"     
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xsi:schemaLocation="urn:mpeg:mpeg21:2002:02-DIDL-NS 
    http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/did/didl.xsd
    urn:mpeg:mpeg21:2002:01-DII-NS 
    http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/dii/dii.xsd">"""


    def _getTopItem(self, lxmlNode):
        ## Wrappers:
        pid, modified, mimetype, pidlocation = '', '', "application/xml", ''
        
#1:     Get persistentIdentifier:
        pidlist = lxmlNode.xpath('//didl:DIDL/didl:Item/didl:Descriptor/didl:Statement/dii:Identifier/text()', namespaces=self._nsMap)
        if len(pidlist) > 0:
            pid = pidlist[0].strip()
            if not comm.isURNNBN(pid):
                raise ValidateException(formatExceptionLine(EXCEPTION0 + pid, prefix=STR_DIDL))
        else:
            raise ValidateException(formatExceptionLine(EXCEPTION1, prefix=STR_DIDL))

#2:     Get toplevel modificationDate: comm.isISO8601()
        tl_modified = lxmlNode.xpath('//didl:DIDL/didl:Item/didl:Descriptor/didl:Statement/dcterms:modified/text()', namespaces=self._nsMap)
        ## Check op geldig/aanwezigheid tlModified, anders exception:
        if len(tl_modified) > 0 and not comm.isISO8601(tl_modified[0]):
            raise ValidateException(formatExceptionLine(EXCEPTION2 + tl_modified[0], prefix=STR_DIDL))
        elif len(tl_modified) == 0:
            raise ValidateException(formatExceptionLine(EXCEPTION3, prefix=STR_DIDL))

        ## Get all modified dates:
        all_modified = lxmlNode.xpath('//didl:Item/didl:Descriptor/didl:Statement/dcterms:modified/text()', namespaces=self._nsMap)
        
        ## Get most recent date from all items, to add to toplevelItem:
        if len(all_modified) > 0:
            datedict = {}
            for date in all_modified:
                if comm.isISO8601(date.strip()):
                    #datedict[parseDate(date.strip())] = date.strip()
                    pd = parseDate(date.strip())
                    datedict["%s %s" % (str(pd.date()), str(pd.time()))] = date.strip()
                    
            ## Get first sorted key:
            for key in reversed(sorted(datedict.iterkeys())):
                modified = datedict[key]
                break
        if not tl_modified[0].strip() == modified:
            self.do.logMsg(self._identifier, LOGGER1, prefix=STR_DIDL)
            
#3:     Get PidResourceMimetype
        mimetypelist = lxmlNode.xpath('//didl:DIDL/didl:Item/didl:Component/didl:Resource/@mimeType', namespaces=self._nsMap)
        if len(mimetypelist) > 0:
            mimetype = mimetypelist[0].strip()
            if not comm.isMimeType(mimetype):
                self.do.logMsg(self._identifier, LOGGER2 + mimetype , prefix=STR_DIDL)

#4:     Get PidResourceLocation:
        pidlocation = self._findAndBindFirst(lxmlNode, '%s',
        '//didl:DIDL/didl:Item/didl:Component/didl:Resource/@ref',
        '//didl:DIDL/didl:Item/didl:Component/didl:Resource/text()'
        '//didl:Item/didl:Item[didl:Descriptor/didl:Statement/rdf:type/@rdf:resource="info:eu-repo/semantics/humanStartPage"]/didl:Component/didl:Resource/@ref', #DIDL 3.0
        '//didl:Item/didl:Item[didl:Descriptor/didl:Statement/rdf:type/@resource="info:eu-repo/semantics/humanStartPage"]/didl:Component/didl:Resource/@ref', #DIDL 3.0, without @rdf:resource
        '//didl:Item/didl:Item[didl:Descriptor/didl:Statement/dip:ObjectType/text()="info:eu-repo/semantics/humanStartPage"]/didl:Component/didl:Resource/@ref', #fallback DIDL 2.3.1
        '//didl:Item/didl:Item[didl:Descriptor/didl:Statement/rdf:type/@rdf:resource="info:eu-repo/semantics/objectFile"]/didl:Component/didl:Resource/@ref', #fallback DIDL 3.0
        '//didl:Item/didl:Item[didl:Descriptor/didl:Statement/rdf:type/@resource="info:eu-repo/semantics/objectFile"]/didl:Component/didl:Resource/@ref', #fallback DIDL 3.0, without @rdf:resource
        '//didl:Item/didl:Item[didl:Descriptor/didl:Statement/dip:ObjectType/text()="info:eu-repo/semantics/objectFile"]/didl:Component/didl:Resource/@ref' #fallback DIDL 2.3.1
        ).strip()

        if pidlocation == '':
            raise ValidateException(formatExceptionLine(EXCEPTION4, prefix=STR_DIDL))
        if not comm.isURL(pidlocation):
            raise ValidateException(formatExceptionLine(EXCEPTION5 + pidlocation, prefix=STR_DIDL))
        
        return """<didl:Item>
        <didl:Descriptor><didl:Statement mimeType="application/xml"><dii:Identifier>%s</dii:Identifier></didl:Statement></didl:Descriptor>
        <didl:Descriptor><didl:Statement mimeType="application/xml"><dcterms:modified>%s</dcterms:modified></didl:Statement></didl:Descriptor>
        <didl:Component><didl:Resource mimeType="%s" ref="%s"/></didl:Component>""" % (escapeXml(pid), modified, escapeXml(mimetype), comm.urlQuote(pidlocation))

    def _getDescriptiveMetadata(self, lxmlNode):
    ## This always normalizes to rdf namespace, without warning/message
        descriptiveMetadataItem = lxmlNode.xpath('//didl:DIDL/didl:Item/didl:Item[didl:Descriptor/didl:Statement/rdf:type/@rdf:resource="info:eu-repo/semantics/descriptiveMetadata"]', namespaces=self._nsMap)
        if len(descriptiveMetadataItem) == 0: #Fallback to @resource (no rdf nmsp), if available...
            descriptiveMetadataItem = lxmlNode.xpath('//didl:DIDL/didl:Item/didl:Item[didl:Descriptor/didl:Statement/rdf:type/@resource="info:eu-repo/semantics/descriptiveMetadata"]', namespaces=self._nsMap)
            if len(descriptiveMetadataItem) > 0: self.do.logMsg(self._identifier, LOGGER3, prefix=STR_DIDL)
        if len(descriptiveMetadataItem) == 0: #Fallback to dip namespace, if available...
            descriptiveMetadataItem = lxmlNode.xpath('//didl:DIDL/didl:Item/didl:Item[didl:Descriptor/didl:Statement/dip:ObjectType/text()="info:eu-repo/semantics/descriptiveMetadata"]', namespaces=self._nsMap)
            if len(descriptiveMetadataItem) > 0: self.do.logMsg(self._identifier, LOGGER4, prefix=STR_DIDL)
        if len(descriptiveMetadataItem) > 0:
            #look for first DMI containing MODS:
            dmi_mods = None
            dmItem = None
            for dmi in descriptiveMetadataItem:
                node = dmi.xpath('self::didl:Item//mods:mods', namespaces=self._nsMap)
                if len(node) > 0: #Found MODS:
                    dmi_mods = node[0]
                    dmItem = dmi
                    break
            else:
                raise ValidateException(formatExceptionLine(EXCEPTION6, prefix=STR_DIDL))
                
            item_template = """<didl:Item>
                                    <didl:Descriptor>
                                        <didl:Statement mimeType="application/xml">
                                            <rdf:type rdf:resource="info:eu-repo/semantics/descriptiveMetadata"/>
                                        </didl:Statement>
                                    </didl:Descriptor>
                                    %s%s<didl:Component>
                                        <didl:Resource mimeType="application/xml">
                                           %s 
                                        </didl:Resource>
                                    </didl:Component>
                                </didl:Item>""" % (self._getIdentifierDescriptor(dmItem), self._getDateModifiedDescriptor(dmItem), tostring(dmi_mods))
        else:
            raise ValidateException(formatExceptionLine(EXCEPTION7, prefix=STR_DIDL))
        return item_template
   
    def _getDateModifiedDescriptor(self, lxmlNode):
        #4: Check geldigheid datemodified (feitelijk verplicht, hoewel vaak niet geimplemeteerd...)
        modified = lxmlNode.xpath('self::didl:Item/didl:Descriptor/didl:Statement/dcterms:modified/text()', namespaces=self._nsMap)
        if len(modified) > 0 and comm.isISO8601(modified[0]):
            return descr_templ % ('<dcterms:modified>'+modified[0].strip()+'</dcterms:modified>')
        elif len(modified) > 0:
            self.do.logMsg(self._identifier, LOGGER5 + modified[0], prefix=STR_DIDL)
        return ''

    def _getIdentifierDescriptor(self, lxmlNode):
        # Check geldige Identifier (feitelijk verplicht, hoewel vaak niet geimplemeteerd...) 
        idee = lxmlNode.xpath('self::didl:Item/didl:Descriptor/didl:Statement/dii:Identifier/text()', namespaces=self._nsMap)
        if len(idee) > 0:
            return descr_templ % ('<dii:Identifier>'+escapeXml(idee[0].strip())+'</dii:Identifier>')
        else:
            return ''

    def _getObjectfiles(self, lxmlNode):              
        of_container = ''
        objectfiles = lxmlNode.xpath('//didl:DIDL/didl:Item/didl:Item[didl:Descriptor/didl:Statement/rdf:type/@rdf:resource="info:eu-repo/semantics/objectFile"]', namespaces=self._nsMap)
        if len(objectfiles) ==0:
            objectfiles = lxmlNode.xpath('//didl:DIDL/didl:Item/didl:Item[didl:Descriptor/didl:Statement/rdf:type/@resource="info:eu-repo/semantics/objectFile"]', namespaces=self._nsMap)
            if len(objectfiles) > 0: self.do.logMsg(self._identifier, LOGGER6, prefix=STR_DIDL)
        if len(objectfiles) ==0:
            objectfiles = lxmlNode.xpath('//didl:DIDL/didl:Item/didl:Item[didl:Descriptor/didl:Statement/dip:ObjectType/text()="info:eu-repo/semantics/objectFile"]', namespaces=self._nsMap)
            if len(objectfiles) > 0: self.do.logMsg(self._identifier, LOGGER7, prefix=STR_DIDL)
        for objectfile in objectfiles:
        #1:Define correct ObjectFile descriptor:
            of_container += '<didl:Item><didl:Descriptor><didl:Statement mimeType="application/xml"><rdf:type rdf:resource="info:eu-repo/semantics/objectFile"/></didl:Statement></didl:Descriptor>' 
            
        #2: Check geldige Identifier (feitelijk verplicht, hoewel vaak niet geimplemeteerd...) 
            pi = objectfile.xpath('self::didl:Item/didl:Descriptor/didl:Statement/dii:Identifier/text()', namespaces=self._nsMap)
            if len(pi) > 0:
                of_container += descr_templ % ('<dii:Identifier>'+escapeXml(pi[0].strip())+'</dii:Identifier>') 
                            
        #3: Check op geldige AccessRights:
            arights = objectfile.xpath('self::didl:Item/didl:Descriptor/didl:Statement/dcterms:accessRights/text()', namespaces=self._nsMap)
            if len(arights) > 0:
                for key, value in accessRights.iteritems():
                    if arights[0].strip().lower().find(key) >= 0:
                        of_container += descr_templ % ('<dcterms:accessRights>'+value+'</dcterms:accessRights>')                        
                        break
                else:
                    raise ValidateException(formatExceptionLine(arights[0] + EXCEPTION12, prefix=STR_DIDL))
            else:
                raise ValidateException(formatExceptionLine(EXCEPTION8, prefix=STR_DIDL))
                                                
        #4: Check geldige datemodified (feitelijk verplicht, hoewel vaak niet geimplemeteerd...)
            modified = objectfile.xpath('self::didl:Item/didl:Descriptor/didl:Statement/dcterms:modified/text()', namespaces=self._nsMap)
            if len(modified) > 0 and comm.isISO8601(modified[0]):
                of_container += descr_templ % ('<dcterms:modified>'+modified[0].strip()+'</dcterms:modified>')   
                
        #5: Check for 'file' description:
            descr = objectfile.xpath('self::didl:Item/didl:Descriptor/didl:Statement/dc:description/text()', namespaces=self._nsMap)
            if len(descr) > 0:
                of_container += descr_templ % ('<dc:description>'+escapeXml(descr[0].strip())+'</dc:description>')  
                
        ## SKIPPING: Not in EduStandaard.            
        #6.0: Check for embargo:
        #    embargo = objectfile.xpath('self::didl:Item/didl:Descriptor/didl:Statement/dcterms:available/text()', namespaces=self._nsMap)
        #    if len(embargo) > 0 and comm.isISO8601(embargo[0]):
        #        of_container += descr_templ % ('<dcterms:available>'+embargo[0].strip()+'</dcterms:available>')
                
        ## SKIPPING: Not in EduStandaard.
        #6.1: Check for dateSubmitted:        
        #    dembargo = objectfile.xpath('self::didl:Item/didl:Descriptor/didl:Statement/dcterms:dateSubmitted/text()', namespaces=self._nsMap)
        #    if len(dembargo) > 0 and comm.isISO8601(dembargo[0]):
        #        of_container += descr_templ % ('<dcterms:dateSubmitted>'+dembargo[0].strip()+'</dcterms:dateSubmitted>')
        #    else:
        #        #6.2: Check for issued (depricated, normalize to dateSubmitted):
        #        issued = objectfile.xpath('self::didl:Item/didl:Descriptor/didl:Statement/dcterms:issued/text()', namespaces=self._nsMap)
        #        if len(issued) > 0 and comm.isISO8601(issued[0]):
        #            of_container += descr_templ % ('<dcterms:dateSubmitted>'+issued[0].strip()+'</dcterms:dateSubmitted>')  

            
        #7: Check for published version(author/publisher):
            pubVersion = objectfile.xpath('self::didl:Item/didl:Descriptor/didl:Statement/rdf:type/@rdf:resource', namespaces=self._nsMap)
            if len(pubVersion) > 0: ## Both (author/publisher) may be available: we'll take the first one...
                for key, value in pubVersions.iteritems():
                    if pubVersion[0].strip().lower().find(key) >= 0:
                        of_container += descr_templ % ('<rdf:type rdf:resource="'+value+'"/>')                                
                        break

        #8:Check for MANDATORY resources and mimetypes:
            didl_resources = objectfile.xpath('self::didl:Item/didl:Component/didl:Resource[@mimeType and @ref]', namespaces=self._nsMap)
            resources = ''
            _url_list = [ ]
            for resource in didl_resources:
                mimeType = resource.xpath('self::didl:Resource/@mimeType', namespaces=self._nsMap)
                uri = resource.xpath('self::didl:Resource/@ref', namespaces=self._nsMap)
                ## We need both mimeType and URI: (MIMETYPE is required by DIDL schema, @ref not).
                if len(mimeType) > 0 and len(uri) > 0:
                    if not comm.isMimeType(mimeType[0]):
                        self.do.logMsg(self._identifier, LOGGER8 + mimeType[0], prefix=STR_DIDL)
                    if comm.isURL(uri[0].strip()):
                        resources += """<didl:Resource mimeType="%s" ref="%s"/>""" % (escapeXml(mimeType[0].strip()), escapeXml(comm.urlQuote(uri[0].strip())))
                        _url_list.append("""<didl:Resource mimeType="%s" ref="%s"/>""" % (escapeXml(mimeType[0].strip()), escapeXml(comm.urlQuote(uri[0].strip()))))
                    else:
                        raise ValidateException(formatExceptionLine(EXCEPTION9 + uri[0], prefix=STR_DIDL))
                        
            if resources != '':
                of_container += """<didl:Component>
                %s
            </didl:Component>""" % (resources)
            else:
                raise ValidateException(formatExceptionLine(EXCEPTION10, prefix=STR_DIDL))            
            of_container += '</didl:Item>'
        return of_container
    
    
    def _getHumanStartPage(self, lxmlNode):
        
        didl_hsp_item = lxmlNode.xpath('//didl:Item/didl:Item[didl:Descriptor/didl:Statement/rdf:type/@rdf:resource="info:eu-repo/semantics/humanStartPage"]', namespaces=self._nsMap)
        if len(didl_hsp_item) == 0:
            didl_hsp_item = lxmlNode.xpath('//didl:Item/didl:Item[didl:Descriptor/didl:Statement/rdf:type/@resource="info:eu-repo/semantics/humanStartPage"]', namespaces=self._nsMap)
            if len(didl_hsp_item) > 0:
                self.do.logMsg(self._identifier, LOGGER9, prefix=STR_DIDL)
            if len(didl_hsp_item) == 0:
                didl_hsp_item = lxmlNode.xpath('//didl:Item/didl:Item[didl:Descriptor/didl:Statement/dip:ObjectType/text()="info:eu-repo/semantics/humanStartPage"]', namespaces=self._nsMap)
                if len(didl_hsp_item) > 0:
                    self.do.logMsg(self._identifier, LOGGER10, prefix=STR_DIDL)
                if len(didl_hsp_item) == 0:
                    self.do.logMsg(self._identifier, LOGGER11, prefix=STR_DIDL)
                    return ""
        
        uriref  =  didl_hsp_item[0].xpath('self::didl:Item/didl:Component/didl:Resource/@ref', namespaces=self._nsMap)
        mimetype = didl_hsp_item[0].xpath('self::didl:Item/didl:Component/didl:Resource/@mimeType', namespaces=self._nsMap)
                
        if len(mimetype) == 0:
            self.do.logMsg(self._identifier, LOGGER13, prefix=STR_DIDL)
        
        if len(mimetype) > 0 and not comm.isMimeType(mimetype[0]):
            self.do.logMsg(self._identifier, LOGGER12 + mimetype[0], prefix=STR_DIDL)
        
        if len(uriref) == 0 or not comm.isURL(uriref[0]):
            raise ValidateException(formatExceptionLine(EXCEPTION11, prefix=STR_DIDL))
                
        return """<didl:Item>
                    <didl:Descriptor>
                        <didl:Statement mimeType="application/xml">
                            <rdf:type rdf:resource="info:eu-repo/semantics/humanStartPage"/>
                        </didl:Statement>
                    </didl:Descriptor>
                    <didl:Component>
                        <didl:Resource ref="%s" mimeType="%s"/>
                    </didl:Component>
                </didl:Item>""" % (escapeXml(comm.urlQuote(uriref[0].strip())), escapeXml(mimetype[0]))
    
        
    def _findAndBindFirst(self, node, template, *xpaths):
        ## Will bind only the FIRST (xpath match/record) to the template. It will never return more than one templated element...
        items = []
        for p in xpaths:
            items += node.xpath(p, namespaces=self._nsMap)
            if len(items)>1:
                break
        for item in items:
            return template % escapeXml(item)
        return ''

    def __str__(self):
        return 'Normalize_nl_DIDL'
