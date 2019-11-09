# -*- coding: utf-8 -*-
from meresco.core import Observable
from datetime import datetime

from time import gmtime, strftime
from xml.sax.saxutils import escape as xmlEscape
from os.path import join, isdir, isfile, basename, abspath, getsize
from os import rename, listdir, remove, makedirs, link
import mmap
from escaping import escapeFilename, unescapeFilename
from dateutil.parser import parse as parseDate

from lxml import etree
from lxml.etree import _ElementTree, tostring, parse as lxmlParse

import logging
import logging.handlers

# Max number of backup files to be created by RotatingFileHandler, before overwriting them:
BACKUPCOUNT = 5

# Max logfilesize:
MAXLOGSIZE = 10485760

RSS_TEMPLATE = """<item>
    <title>%(title)s</title>
    <description>%(description)s</description>
    <guid>%(identifier)s</guid>
    <pubDate>%(date)s</pubDate>
    <link>%(link)s</link>
</item>"""

class Logger(Observable):

    def __init__(self, logfileDir, enabled=True):
        Observable.__init__(self)
        self._enabled = enabled
        self._logfileDir = logfileDir           
        #self._logger = logging.getLogger('Logger')
        #self._logger.setLevel(logging.WARNING)
        
        #self._formatter = logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%dT%H:%M:%SZ")
            
        if not isdir(self._logfileDir):
            makedirs(self._logfileDir)
            
        print "RSS Logger directory:", self._logfileDir


    def logMsg(self, identifier, logmsg, prefix=None):
        if self._enabled:
            str_logline = identifier + " " + logmsg if prefix is None else identifier + " " + prefix +" "+ logmsg
            #print "LOGGER RECEIVED:", str_logline
            #LOG_FILENAME = join(self._logfileDir, escapeFilename(identifier.split(':', 1 )[0]))

            ## Use python logging module:
            #handler = logging.handlers.RotatingFileHandler((LOG_FILENAME), maxBytes=MAXLOGSIZE, backupCount=BACKUPCOUNT)
            #handler.setFormatter(self._formatter)
            #self._logger.addHandler(handler)
            #self._logger.warning( str_logline )
            #self._logger.removeHandler(handler)
            
            ## OR -> create our own logfile...
            #with open(LOG_FILENAME, "a") as logFile:
            #    try:
            #        logFile.write(str(strftime("%Y%m%dT%H:%M:%SZ", gmtime())) + " " + identifier + " " + self._msg_prefix+logmsg + "\n")
            #        logFile.flush()
            #    finally:                    
            #        logFile.close()
            
            # OR -> Custom RotatedFile: http://www.snip2code.com/Snippet/4441/Rotating-file-implementation-for-python-/ 
            
            logger = getRssLogger(identifier.split(':', 1 )[0], self._logfileDir) #repositoryId, logfileDir
            logger.warning( str_logline )
            
            
                                                       
    def getLogLinesAsRssItems(self, repositoryId, maxlines):
        """Geeft RSS <item> representatie van loglines terug"""
        #print "Getting loglines for", repositoryId, maxlines
        buffer = ''
        lines = self._getUniqueLogLines(repositoryId, maxlines)       
        #lines = self._tail(repositoryId, maxlines)
        if lines:
            burl, prfx = None, None
            for line in reversed(lines):                
                
                lineparts = line.split(' ', 2)
                
                # Get baseUrl and metadataperfix from meta part only once:
                # Beware: We'll assume the latest warning has the most recent (and probably correct) repository settings. 
                if burl is None:
                    burl, prfx = self._getMetaPartStuff(lineparts[1])
                
                oai_id = lineparts[1].split(':', 1 )[1]
                rssData = {
                'title': xmlEscape( oai_id ),
                'description': xmlEscape( lineparts[2] ),
                'identifier': xmlEscape( lineparts[1] ),
                'date': xmlEscape( str((parseDate(lineparts[0], ignoretz=True)).date()) ),
                'link': xmlEscape( ('%s?verb=GetRecord&identifier=%s&metadataPrefix=%s') % (burl, oai_id, prfx)   )             
                }
                buffer += str(RSS_TEMPLATE % rssData)
            
        return buffer
            #https://github.com/seecr/meresco-components/blob/master/meresco/components/rss.py

    def _tail(self, rgId, n):
        """Returns last n lines from the filename. No exception handling.
        http://stackoverflow.com/questions/136168/get-last-n-lines-of-a-file-with-python-similar-to-tail
        """
        if isfile(join(self._logfileDir, rgId)):
            size = getsize(join(self._logfileDir, rgId))
            with open(join(self._logfileDir, rgId), "rb") as f:
                # for Windows the mmap parameters are different
                fm = mmap.mmap(f.fileno(), 0, mmap.MAP_SHARED, mmap.PROT_READ)
                try:
                    for i in xrange(size - 1, -1, -1):
                        if fm[i] == '\n':
                            n -= 1
                            if n == -1:
                                break
                    return fm[i + 1 if i else 0:].splitlines()
                except (OSError, IOError):
                    return[]
                finally:
                    fm.close()
        else:
            return[]


    def _getMetaPartStuff(self, uploadId):
        meta = self._getPart(uploadId, 'meta')
        if meta is not None:
            baseu = meta.xpath("//meta:repository/meta:baseurl/text()", namespaces={'meta':'http://meresco.org/namespace/harvester/meta'})
            prefix = meta.xpath("//meta:repository/meta:metadataPrefix/text()", namespaces={'meta':'http://meresco.org/namespace/harvester/meta'})
            return baseu[0], prefix[0]
        return None, None


    def _getPart(self, recordId, partname):
        if self.call.isAvailable(recordId, partname) == (True, True):
            stream = self.call.getStream(recordId, partname)
            return lxmlParse(stream)
        return None


    def _getUniqueLogLines(self, repositoryId, maxlines):
        log_dict = {}
        bckpcnt = 0
        #reversed... CON: Reads complete file into memory...
        #for line in reversed(open(join(self._logfileDir, "ut"), 'r').readlines()):
        while len(log_dict) < maxlines and bckpcnt <= BACKUPCOUNT:
            #Check which file to open:
            file_name = repositoryId if bckpcnt == 0 else (repositoryId +'.'+ str(bckpcnt))
            #print "Check isfile...", file_name
            if isfile(join(self._logfileDir, file_name)):
                #print "Opening log file...", file_name
                # to open a file, process its contents, and make sure to close it, you can simply do:
                with open(join(self._logfileDir, file_name), 'r') as file:
                    #print "LOGfile OPENED..."
                    for line in file:
                        log_dict [line.split(' ', 2)[2]] = line #log_dict [line.split(' ', 3)[3]] = line
            if len(log_dict) >= maxlines:
                #print "Reached max lines...", maxlines
                break
            bckpcnt = bckpcnt+1
        #print "Return UNIQUE:", str(len(log_dict))
        #for v in sorted(log_dict.values()):
        #    print v
        return sorted(log_dict.values())


def getRssLogger(repositoryId, logfileDir):
    
    logger = logging.getLogger(repositoryId)
    
    if len (logger.handlers) > 0:
        #print "Logger Available..."
        return logger
    
    # No handlers set yet, this is a new logger from the factory...
    logger.setLevel(logging.WARNING)

    LOG_FILENAME = join(logfileDir,  escapeFilename(repositoryId) )
    rfh = logging.handlers.RotatingFileHandler((LOG_FILENAME), maxBytes=MAXLOGSIZE, backupCount=BACKUPCOUNT)
    
    formatter = logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%dT%H:%M:%SZ")
    rfh.setFormatter(formatter)
    
    logger.addHandler(rfh)
    #print "Created new Logger..."
    return logger
