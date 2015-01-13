import gzip,os,urllib,httplib
from datetime import datetime
from os import listdir
from os.path import isfile, join

class Generator:
    BASE_PATH = ''
    BASE_URL  = ''
    SITE_URL  = ''
    GZIP      = False
    PING      = False
    _maps     = {}
    _cities   = {}

    def __init__(self,options={}):
        if not 'base_path' in options:
            raise Exception('base_path must be supplied')

        if not 'site_url' in options:
            raise Exception('site_url must be supplied')

        self.SITE_URL = options['site_url']
        if self.SITE_URL[-1:] != '/':
            self.SITE_URL += '/'

        self.BASE_PATH = options['base_path']
        if self.BASE_PATH[-1:] != '/':
            self.BASE_PATH += '/'

        self.BASE_URL  = options.get('base_url',self.SITE_URL)
        if self.BASE_URL[-1:] != '/':
            self.BASE_URL += '/'

        self.GZIP      = options.get('gzip',False)
        self.PING      = options.get('ping',False)
        self.mkdir_p(self.BASE_PATH)
        self.clear()

    def finish(self):
        self.close_sitemaps()
        options = {
            'gzip': self.GZIP,
            'type':'index',
            'filename': join(self.BASE_PATH,'sitemap')
        }
        index = IndexBuilder(options)
        for f in self.files():
            index.add_url(join(self.BASE_URL,f),{'last_modified':datetime.now(),'change_frequency':'daily','priority':0.9})
        index.close()

        if self.PING:
            self.ping()

    def ping(self):
        sitemap_uri = join(self.BASE_PATH,"sitemap.xml")
        if self.GZIP:
          sitemap_uri = join(sitemap_uri,".gz")

        params = urllib.urlencode({'sitemap':sitemap_uri})

        conn = httplib.HTTPConnection("www.google.com")
        conn.request("GET", "/webmasters/tools/ping?%s"%(params))

        conn = httplib.HTTPConnection("www.bing.com")
        conn.request("GET", "/ping?%s"%(params))

    def close_sitemaps(self):
        for sitemap in self._maps.values():
            sitemap.close()
        self._maps = {}

    def files(self):
        files = []
        for f in listdir(self.BASE_PATH):
            if isfile(join(self.BASE_PATH,f)) and 'xml' in f and not 'tmp' in f:
                files.append(f)
        return files

    def clear(self):
        for f in self.files():
            os.unlink(join(self.BASE_PATH,f))

    def sitemap_for_label(self,label):
        if label in self._maps:
            return self._maps[label]

        parts = label.split('_')
        path = label
        options = {
            'gzip': self.GZIP,
            'type':'static',
            'start_part_id':0,
            'partial_update':False,
            'filename': self.BASE_PATH+path
        }
        self._maps[label] = Builder(options)
        return self._maps[label] 

    def add_url(self,label,location,options = {},callback=None):
        sitemap = self.sitemap_for_label(label)
        if location[0] == '/':
            location = location[1:]
        sitemap.add_url(self.SITE_URL+location, options)
        if callback:
            callback()

    def parse_label(self,uri):
        label = ''
        parts = uri.split('/')
        if len(parts) > 1:
            parts.reverse()
            uri_parts = filter(len,parts)
            if uri_parts[len(uri_parts) - 1] in self._cities:
                label += join(uri_parts.pop(),'_')
            label += uri_parts.pop()
        else:
            return parts[0]

        return label

    def mkdir_p(self,path):
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
            except OSError as exc: # Python >2.5
                if exc.errno == errno.EEXIST and os.path.isdir(path):
                    print exc
                else: 
                    raise

class Builder:
    MAX_URLS = 50000
    HEADER_NAME = 'urlset'
    HEADER_ATTRIBUTES = {
      'xmlns':'http://www.sitemaps.org/schemas/sitemap/0.9',
      'xmlns:xsi':'http://www.w3.org/2001/XMLSchema-instance',
      'xsi:schemaLocation':'http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd'
    }

    def __init__(self,options):
        self._timezone       = options.get('timezone', 'Z')
        self._gzip           = options.get('gzip',False)
        self._max_urls       = options.get('max_urls',self.MAX_URLS)
        self._type           = options.get('type')
        self._filepaths      = []
        self._parts          = options.get('start_part_id',0)
        self._partial_update = options.get('partial_update',False)

        self._filename         = options.get('filename')
        self._current_filename = None
        self._tmp_filename     = None
        self._target           = self.get_writer()

        self._level = 0
        self._opened_tags = []
        self.init_document()
        self._urls  = 0

    def get_writer(self):
        filename = self._filename
        if self._parts > 0 and self._type != 'index':
            filename = "%s_%d.xml"%(filename,self._parts)
        else:
            filename = "%s.xml"%(filename)

        if self._gzip:
            filename = "%s.gz"%(filename)
        writer = self.open_writer(filename)
        return writer

    def open_writer(self,filename):
        self._current_filename = filename
        self._tmp_filename     = filename + ".tmp"
        self._filepaths.append(filename)
        if self._gzip:
            return gzip.open(self._tmp_filename,'w')
        else:
            return open(self._tmp_filename,'w')
      
    def close(self):
        self.close_document()
        try:
            self._target.close()
        except Exception as inst:
            print repr(inst)

        if isfile(self._current_filename):
            os.unlink(self._current_filename)

        os.rename(self._tmp_filename, self._current_filename)

    def format_iso8601(self, obj, timezone):
        updated = '%Y-%m-%dT%H:%M:%S' + timezone
        return obj.strftime(updated)

    def add_url(self,location, options={}):
        if self._max_urls == self._urls:
            self.rotate(options.get('id',None))
        self.open_tag('url')
        self.tag('loc', location)
        if 'last_modified' in options:
            self.tag('lastmod', self.format_iso8601(options['last_modified'],self._timezone))
        self.tag('changefreq', options.get('change_frequency','weekly'))
        if 'priority' in options:
            self.tag('priority', options['priority'])
        self.close_tag('url')
        self._urls += 1

    def filepaths(self):
        return self._filepaths

    def target(self):
        return self._target

    def init_document(self):
        self._urls = 0
        self._target.write('<?xml version="1.0" encoding="UTF-8"?>')
        self.newline()
        self.open_tag(self.HEADER_NAME, self.HEADER_ATTRIBUTES)

    def rotate(self,part_nr=None):
        # write out the current document and start writing into a new file
        self.close()
        if part_nr:
            self._parts = part_nr
        else:
            self._parts += 1

        self._target = self.get_writer()
        self.init_document()

    def close_document(self):
        self._opened_tags.reverse()
        for name in self._opened_tags:
            self.close_tag(name)

    def indent(self):
        self._target.write("  " * self._level)

    def newline(self):
        self._target.write("\n")

    # opens a tag, bumps up level but doesn't require a block
    def open_tag(self,name, attrs={}):
        self.indent()
        self.start_tag(name, attrs)
        self.newline()
        self._level += 1
        self._opened_tags.append(name)

    def start_tag(self,name, attrs={}):
        attrs = [ "%s=\"%s\""%(k,v) for k, v in attrs.items() ]
        self._target.write("<%s %s>"%(name,' '.join(attrs)))

    def tag(self,name, content, attrs = {}):
        self.indent()
        self.start_tag(name, attrs)
        self._target.write(str(content).replace('&', '&amp;'))
        self.end_tag(name)
        self.newline()

    def end_tag(self,name):
        self._target.write("</%s>"%(name))

    # closes a tag block by decreasing the level and inserting a close tag
    def close_tag(self,name):
      self._opened_tags.pop()
      self._level -= 1
      self.indent()
      self.end_tag(name)
      self.newline()

class IndexBuilder(Builder):
    HEADER_NAME = 'sitemapindex'
    HEADER_ATTRIBUTES = {'xmlns':'http://www.sitemaps.org/schemas/sitemap/0.9'}

    def add_url(self,location, options={}):
        self.open_tag('sitemap')
        self.tag('loc', location)
        if 'last_modified' in options:
            self.tag('lastmod', self.format_iso8601(options['last_modified'],self._timezone))
        self.close_tag('sitemap')

__all__ = [Builder,IndexBuilder]
