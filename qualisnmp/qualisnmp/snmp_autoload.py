"""
"""

from quali_snmp import QualiSnmp
from collections import OrderedDict


class AutoLoad(object):

    def __init__(self, ip, port=161, community='private'):
        """ Initialize SNMP environment and read tables.

        entPhysicalTable is saved in self.entPhysicalTable
        ifTable is saved in self.ifTable

        :param ip: device IP.
        :param port: device SNMP port.
        :param community: device community.
        """
        super(AutoLoad, self).__init__()

        self.snmp = QualiSnmp(ip, port, community)
        self.entPhysicalTable = self.snmp.walk(('ENTITY-MIB', 'entPhysicalTable'))
        self.ifTable = self.snmp.walk(('IF-MIB', 'ifTable'))

    def get_hierarchy(self):
        """
        :return: device hierarchy in the following format:
        |        {chassis index: {'modules': {module index 1: [port indexes], ...},
        |                         'ports': [port indexes]}
        |        ...}
        :todo: add support for modules...
        :todo: add support for multi chassis
        """

        hierarchy = {}
        for chassis_index in self.entPhysicalTable.filter_by_column('Class', "'chassis'").keys():
            hierarchy[chassis_index] = {'modules': {}, 'ports': []}
            modules = self.entPhysicalTable.filter_by_column('Class', '9')
            if modules:
                hierarchy[chassis_index]['modules'] = modules.keys()
            ports = self.entPhysicalTable.filter_by_column('Class', "'port'")
            chassis_ports = ports.filter_by_column('ContainedIn', str(chassis_index))
            hierarchy[chassis_index]['ports'] = chassis_ports.sort_by_column('ParentRelPos').keys()

        return hierarchy

    def get_mapping(self):
        """
        :return: simple mapping from entPhysicalTable index to ifTable index:
        |        {entPhysicalTable index: ifTable index, ...}
        :todo: add support for modules...
        """

        mapping = OrderedDict()
        entAliasMappingTable = self.snmp.walk(('ENTITY-MIB', 'entAliasMappingTable'))
        for port in self.entPhysicalTable.filter_by_column('Class', "'port'"):
            mapping[port] = int(entAliasMappingTable[port]
                                ['entAliasMappingIdentifier'].split('.')[-1])

        return mapping
