from distutils.core import setup

setup(
    name='BigSitemap',
    version='0.1.0',
    author='Renato Aquino',
    author_email='renato.aquino@gmail.com',
    packages=['bigsitemap'],
    url='http://pypi.python.org/pypi/BigSitemap/',
    license='LICENSE.txt',
    description='A sitemap generator suitable for applications with greater than 50,000 URLs.',
    long_description=open('README.txt').read()
)