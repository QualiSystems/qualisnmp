
from setuptools import setup

setup(name='qualisnmp',
      version='0.1',
      description='SNMP tools for Quali device driver.',
      url='',
      author='Yoram Shamir',
      author_email='yoram-s@qualisystems.com',
      license='',
      packages=['qualisnmp', 'qualisnmp.test'],
      zip_safe=False,
      install_requires=[
          'pysnmp',
          'pysnmp-mibs'
      ])
