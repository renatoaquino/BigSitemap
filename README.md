#BigSitemap

This package was based on the big_sitemap ruby [gem](https://rubygems.org/gems/big_sitemap).

From [BigSitemap](https://rubygems.org/gems/big_sitemap):

>BigSitemap is a Sitemapgenerator suitable for applications with greater than 50,000 URLs. It splits large Sitemaps into multiple files, gzips the files to minimize bandwidth usage...


##Usage

    import bigsitemap

    options = {
        'gzip': True,
        'ping': True,
        'base_url': 'http://cdn.mywebsite.com/sitemaps/',
        'site_url': 'http://www.mywebsite.com/',
        'base_path': '/var/www/cdn/sitemaps'
    }

    sections = ['/','/boats','/cars','/gadgets','/travel']
    places   = ['/parents-house.html','/grocery-store.html']

    generator = bigsitemap.Generator(options)
    for section in sections:
        generator.add_url('sections',section,{'last_modified':datetime.now(),'change_frequency':'daily','priority':0.6})
    for place in places:
        generator.add_url('places',place,{'last_modified':datetime.now(),'change_frequency':'daily','priority':0.6})

    generator.finish() 
    generator.files() #Returns ['sitemap.xml.gz','sections.gz','places.gz']



If your sitemaps grow beyond 50,000 URLs, the sitemap files will be partitioned into multiple files (places_1.xml.gz, places_2.xml.gz, ...).

##Initialization Options

* gzip: Use gzip? Default **False**.
* ping: Ping google and bing on finish? Default **False**.
* base_path: Where to store the sitemap files? **required**
* site_url: What is your website url? **required**
* base_url: If you store the xml files into another host, supply it here. Default **site_url**.


##Change Frequency, Priority and Last Modified

You can control [changefreq](http://www.sitemaps.org/protocol.html#changefreqdef), [priority](http://www.sitemaps.org/protocol.html#prioritydef) and [lastmod](http://www.sitemaps.org/protocol.html#lastmoddef) values for each record individually by passing them as optional arguments when adding URLs:

    generator.add_url('sections',section,{
        'last_modified':datetime.now(),
        'change_frequency':'daily',
        'priority':0.6
    })

##TODO
    - Writer class for dependency injection
    - Automated tests

##Credits
Many thanks to Stateless Systems [statelesssystems.com](statelesssystems.com) for releasing the big_sitemap ruby [gem] (https://rubygems.org/gems/big_sitemap). 