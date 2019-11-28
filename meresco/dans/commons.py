#!/usr/bin/env python
# -*- coding: utf-8 -*-

from re import compile, IGNORECASE
from dateutil.parser import parse as parseDate
import urllib
from urlparse import urlparse, urlunparse

#RegEx:
REG_URNNBN = r'^[uU][rR][nN]:[nN][bB][nN]:[nN][lL](:([a-zA-Z]{2}))?:\d{2}-.+'

REG_RFC3066 = r'^[a-zA-Z]{1,8}(-[a-zA-Z0-9]{2,8})*$'

REG_URL =  (r'^(?:http|ftp|sftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$')

REG_MIMETYPE = r'^(application|audio|example|image|message|model|multipart|text|video)/.{2,}$'


# Compile RegEx's:
patternURL = compile(REG_URL, IGNORECASE)
patternRFC3066 = compile(REG_RFC3066)
patternURNNBN = compile(REG_URNNBN)
patternMIMETYPE = compile(REG_MIMETYPE, IGNORECASE) ## MIME Media-Types taken from: http://www.iana.org/assignments/media-types/media-types.xhtml


#Taken from: http://www.loc.gov/standards/iso639-2/ISO-639-2_utf-8.txt
RFC3066 = ['aa', 'aar', 'ab', 'abk', 'ace', 'ach', 'ada', 'ady', 'ae', 'af', 'afa', 'afh', 'afr', 'ain', 'ak', 'aka', 'akk', 'alb', 'ale', 'alg', 'alt', 'am', 'amh', 'an', 'ang', 'anp', 'apa', 'ar', 'ara', 'arc', 'arg', 'arm', 'arn', 'arp', 'art', 'arw', 'as', 'asm', 'ast', 'ath', 'aus', 'av', 'ava', 'ave', 'awa', 'ay', 'aym', 'az', 'aze', 'ba', 'bad', 'bai', 'bak', 'bal', 'bam', 'ban', 'baq', 'bas', 'bat', 'be', 'bej', 'bel', 'bem', 'ben', 'ber', 'bg', 'bh', 'bho', 'bi', 'bih', 'bik', 'bin', 'bis', 'bla', 'bm', 'bn', 'bnt', 'bo', 'bod', 'bos', 'br', 'bra', 'bre', 'bs', 'btk', 'bua', 'bug', 'bul', 'bur', 'byn', 'ca', 'cad', 'cai', 'car', 'cat', 'cau', 'ce', 'ceb', 'cel', 'ces', 'ch', 'cha', 'chb', 'che', 'chg', 'chi', 'chk', 'chm', 'chn', 'cho', 'chp', 'chr', 'chu', 'chv', 'chy', 'cmc', 'co', 'cop', 'cor', 'cos', 'cpe', 'cpf', 'cpp', 'cr', 'cre', 'crh', 'crp', 'cs', 'csb', 'cu', 'cus', 'cv', 'cy', 'cym', 'cze', 'da', 'dak', 'dan', 'dar', 'day', 'de', 'del', 'den', 'deu', 'dgr', 'din', 'div', 'doi', 'dra', 'dsb', 'dua', 'dum', 'dut', 'dv', 'dyu', 'dz', 'dzo', 'ee', 'efi', 'egy', 'eka', 'el', 'ell', 'elx', 'en', 'eng', 'enm', 'eo', 'epo', 'es', 'est', 'et', 'eu', 'eus', 'ewe', 'ewo', 'fa', 'fan', 'fao', 'fas', 'fat', 'ff', 'fi', 'fij', 'fil', 'fin', 'fiu', 'fj', 'fo', 'fon', 'fr', 'fra', 'fre', 'frm', 'fro', 'frr', 'frs', 'fry', 'ful', 'fur', 'fy', 'ga', 'gaa', 'gay', 'gba', 'gd', 'gem', 'geo', 'ger', 'gez', 'gil', 'gl', 'gla', 'gle', 'glg', 'glv', 'gmh', 'gn', 'goh', 'gon', 'gor', 'got', 'grb', 'grc', 'gre', 'grn', 'gsw', 'gu', 'guj', 'gv', 'gwi', 'ha', 'hai', 'hat', 'hau', 'haw', 'he', 'heb', 'her', 'hi', 'hil', 'him', 'hin', 'hit', 'hmn', 'hmo', 'ho', 'hr', 'hrv', 'hsb', 'ht', 'hu', 'hun', 'hup', 'hy', 'hye', 'hz', 'ia', 'iba', 'ibo', 'ice', 'id', 'ido', 'ie', 'ig', 'ii', 'iii', 'ijo', 'ik', 'iku', 'ile', 'ilo', 'ina', 'inc', 'ind', 'ine', 'inh', 'io', 'ipk', 'ira', 'iro', 'is', 'isl', 'it', 'ita', 'iu', 'ja', 'jav', 'jbo', 'jpn', 'jpr', 'jrb', 'jv', 'ka', 'kaa', 'kab', 'kac', 'kal', 'kam', 'kan', 'kar', 'kas', 'kat', 'kau', 'kaw', 'kaz', 'kbd', 'kg', 'kha', 'khi', 'khm', 'kho', 'ki', 'kik', 'kin', 'kir', 'kj', 'kk', 'kl', 'km', 'kmb', 'kn', 'ko', 'kok', 'kom', 'kon', 'kor', 'kos', 'kpe', 'kr', 'krc', 'krl', 'kro', 'kru', 'ks', 'ku', 'kua', 'kum', 'kur', 'kut', 'kv', 'kw', 'ky', 'la', 'lad', 'lah', 'lam', 'lao', 'lat', 'lav', 'lb', 'lez', 'lg', 'li', 'lim', 'lin', 'lit', 'ln', 'lo', 'lol', 'loz', 'lt', 'ltz', 'lu', 'lua', 'lub', 'lug', 'lui', 'lun', 'luo', 'lus', 'lv', 'mac', 'mad', 'mag', 'mah', 'mai', 'mak', 'mal', 'man', 'mao', 'map', 'mar', 'mas', 'may', 'mdf', 'mdr', 'men', 'mg', 'mga', 'mh', 'mi', 'mic', 'min', 'mis', 'mk', 'mkd', 'mkh', 'ml', 'mlg', 'mlt', 'mn', 'mnc', 'mni', 'mno', 'moh', 'mon', 'mos', 'mr', 'mri', 'ms', 'msa', 'mt', 'mul', 'mun', 'mus', 'mwl', 'mwr', 'my', 'mya', 'myn', 'myv', 'na', 'nah', 'nai', 'nap', 'nau', 'nav', 'nb', 'nbl', 'nd', 'nde', 'ndo', 'nds', 'ne', 'nep', 'new', 'ng', 'nia', 'nic', 'niu', 'nl', 'nld', 'nn', 'nno', 'no', 'nob', 'nog', 'non', 'nor', 'nqo', 'nr', 'nso', 'nub', 'nv', 'nwc', 'ny', 'nya', 'nym', 'nyn', 'nyo', 'nzi', 'oc', 'oci', 'oj', 'oji', 'om', 'or', 'ori', 'orm', 'os', 'osa', 'oss', 'ota', 'oto', 'pa', 'paa', 'pag', 'pal', 'pam', 'pan', 'pap', 'pau', 'peo', 'per', 'phi', 'phn', 'pi', 'pl', 'pli', 'pol', 'pon', 'por', 'pra', 'pro', 'ps', 'pt', 'pus', 'qaa', 'qtz', 'qu', 'que', 'raj', 'rap', 'rar', 'rm', 'rn', 'ro', 'roa', 'roh', 'rom', 'ron', 'ru', 'rum', 'run', 'rup', 'rus', 'rw', 'sa', 'sad', 'sag', 'sah', 'sai', 'sal', 'sam', 'san', 'sas', 'sat', 'sc', 'scn', 'sco', 'sd', 'se', 'sel', 'sem', 'sg', 'sga', 'sgn', 'shn', 'si', 'sid', 'sin', 'sio', 'sit', 'sk', 'sl', 'sla', 'slk', 'slo', 'slv', 'sm', 'sma', 'sme', 'smi', 'smj', 'smn', 'smo', 'sms', 'sn', 'sna', 'snd', 'snk', 'so', 'sog', 'som', 'son', 'sot', 'spa', 'sq', 'sqi', 'sr', 'srd', 'srn', 'srp', 'srr', 'ss', 'ssa', 'ssw', 'st', 'su', 'suk', 'sun', 'sus', 'sux', 'sv', 'sw', 'swa', 'swe', 'syc', 'syr', 'ta', 'tah', 'tai', 'tam', 'tat', 'te', 'tel', 'tem', 'ter', 'tet', 'tg', 'tgk', 'tgl', 'th', 'tha', 'ti', 'tib', 'tig', 'tir', 'tiv', 'tk', 'tkl', 'tl', 'tlh', 'tli', 'tmh', 'tn', 'to', 'tog', 'ton', 'tpi', 'tr', 'ts', 'tsi', 'tsn', 'tso', 'tt', 'tuk', 'tum', 'tup', 'tur', 'tut', 'tvl', 'tw', 'twi', 'ty', 'tyv', 'udm', 'ug', 'uga', 'uig', 'uk', 'ukr', 'umb', 'und', 'ur', 'urd', 'uz', 'uzb', 'vai', 've', 'ven', 'vi', 'vie', 'vo', 'vol', 'vot', 'wa', 'wak', 'wal', 'war', 'was', 'wel', 'wen', 'wln', 'wo', 'wol', 'xal', 'xh', 'xho', 'yao', 'yap', 'yi', 'yid', 'yo', 'yor', 'ypk', 'za', 'zap', 'zbl', 'zen', 'zgh', 'zh', 'zha', 'zho', 'znd', 'zu', 'zul', 'zun', 'zxx', 'zza']


def isURNNBN(pid):
    m = patternURNNBN.match(pid)
    if not m:
        return False
    return True


def isURL(st_url, doQuoting=True):
    '''
    Checks if given url is valid against a RegEx.
    It decodes before it encodes to prevent double encoding.
    :param str_url: The url to be quoted.
    :param doQuoting: boolean, if str_url needs to be unquoted and quoted before testing. Default is True.
    '''
    if doQuoting:
        st_url = urlQuote(st_url)
    bln_isValid = False
    m = patternURL.match(st_url)
    if m:
        bln_isValid = True
    return bln_isValid    


def urlQuote(str_url):
    '''
    Url Quotes the path part of a URL.
    It decodes before it encodes to prevent double encoding.
    :param str_url: The url to be quoted.
    '''
    o = urlparse(str_url)
    _pad = o.path
    _pad = urllib.unquote(_pad)
    _pad = urllib.quote(_pad.encode('utf-8', "xmlcharrefreplace")) #We'll not ignore or throw errors here, but use xml encodng instead.
    # _pad.encode('utf-8', "xmlcharrefreplace") Wait, what happens here?
    # _pad might already be a utf-8 byte string. If, so, Python implicit decodes _pad to unicode (using sys.getdefaultencoding(), which should be utf-8), and then we encode it back to utf-8 byte string...
    # _pad might be unicode string. If, so, we explicitly encode/convert it to utf-8 byte string, and encode all characters not available in utf-8, to xml-chars, which will be available in utf-8...
    # http://nedbatchelder.com/text/unipain.html
    return urlunparse((o.scheme, o.netloc, _pad, o.params, o.query, o.fragment))


def isValidRFC3066(string):
    bln_isValid = False
    if string is not None and string.strip().split('-', 1)[0] in RFC3066:
        m = patternRFC3066.match(string)
        if m:
            bln_isValid = True
    return bln_isValid

def isInt(s):
    if s is None:
        return False
    try: 
        int(s)
    except ValueError:
        return False
    return True


def isMimeType(string):
    m = patternMIMETYPE.match(string)
    if not m:
        return False
    return True


def isISO8601(datestring):
    try:
        parseDate(datestring)
    except ValueError:
        return False
    return True