
from unittest import TestCase

from pysnmp.hlapi import UsmUserData, usmHMACSHAAuthProtocol, usmDESPrivProtocol

from qualisnmp.quali_snmp import QualiSnmp, load_mib
from qualisnmp.snmp_autoload import AutoLoad

ip = '172.25.10.204'
ro_community = 'public'
rw_community = ''
v3_user = UsmUserData('QUALI', 'Password1', 'Live4lol', usmHMACSHAAuthProtocol, usmDESPrivProtocol)


class SnmpTest(TestCase):
    """ SNMP class tests.

    :todo: test with assert.
    """

    def setUp(self):
        self.snmp = QualiSnmp(ip=ip, community=ro_community)

    def testGet(self):

        values = self.snmp.get(('ENTITY-MIB', 'entPhysicalDescr', 7))
        print values

        values = self.snmp.get('1.3.6.1.2.1.1.4.0', '1.3.6.1.2.1.1.1.0')
        print values

        values = self.snmp.get('1.3.6.1.2.1.1.4', '1.3.6.1.2.1.1.1')
        print values

        values = self.snmp.get(('SNMPv2-MIB', 'sysContact'), ('SNMPv2-MIB', 'sysDescr'))
        print values

        values = self.snmp.get(('SNMPv2-MIB', 'sysContact', 0), ('SNMPv2-MIB', 'sysDescr', 0))
        print values

        values = self.snmp.get(('SNMPv2-MIB', 'sysContact', 0), '1.3.6.1.2.1.1.1')
        print values

        values = self.snmp.get(('IF-MIB', 'ifPhysAddress', 7))
        print values

        pass

    def testNext(self):

        values = self.snmp.next(('SNMPv2-MIB', 'sysContact'))
        print values

        values = self.snmp.next(('ENTITY-MIB', 'entPhysicalTable'))
        print values

        pass

    def testWalk(self):

        # Get all entries.
        values = self.snmp.walk(('ENTITY-MIB', 'entPhysicalTable'))
        print values
        # Get column (an attribute for for entries).
        values = self.snmp.walk(('ENTITY-MIB', 'entPhysicalDescr'))
        print values
        # Get row (all attribute of an index).
        values = self.snmp.walk(('ENTITY-MIB', 'entPhysicalTable'), 7)
        print values
        # And even a single cell.
        values = self.snmp.walk(('ENTITY-MIB', 'entPhysicalDescr'), 7)
        print values

        load_mib('IP-MIB')
        values = self.snmp.walk(('IP-MIB', 'ipAddrTable'))
        print values

        values = self.snmp.walk(('IF-MIB', 'ifTable'))
        print values

        values = self.snmp.walk(('IF-MIB', 'ifPhysAddress'))
        print values

        pass

    def testTable(self):
        # Get all entries.
        table = self.snmp.walk(('ENTITY-MIB', 'entPhysicalTable'))
        for row in table.get_rows(10, 11).items():
            print row
        for row in table.get_columns('Class', 'Name').items():
            print row
        for row in table.filter_by_column('Class', '3').items():
            print row
        for row in table.filter_by_column('Class', '3', '10').items():
            print row
        for row in table.sort_by_column('ParentRelPos').items():
            print row
        pass


class AutoLoadTest(TestCase):

    def setUp(self):
        self.autoload = AutoLoad(ip=ip, community=ro_community)

    def testAutoload(self):
        hierarchy = self.autoload.get_hierarchy()
        print hierarchy
        mapping = self.autoload.get_mapping()
        print mapping

        print self.autoload.entPhysicalTable[2]
        print self.autoload.ifTable[mapping[2]]

        pass
