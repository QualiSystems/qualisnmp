"""
This module contains classes and utility functions to implement Quali resource manager Autoload
functionality using SNMP.
"""

from quali_snmp import QualiSnmp
from collections import OrderedDict


class AutoLoad(object):
    """ Base class for Quali SNMP based Autoload functionality. """

    autolad_parents = {"'port'": ["'module'", "'chassis'"],
                       "'powerSupply'": ["'chassis'"],
                       "'module'": ["'chassis'"],
                       "'container'": ["'chassis'"],
                       "'chassis'": []}
    """ Dictionary mapping from autload entity to its valid autoload parents. """

    def __init__(self, ip, port=161, community='private'):
        """ Initialize SNMP environment and read tables.

        Read entPhysicalTable and ifTable.
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

    def get_hierarchy(self, *types):
        """
        :return: device autoload hierarchy in the following format:
        |        {root index: [child1 index, child2 index, ...],
        |         child1 index: [child11 index, child12 index, ...]}
        |        ...}
        :todo: add support for multi chassis
        """

        hierarchy = {}
        ports = self.entPhysicalTable.filter_by_column('Class', "'port'")
        pss = self.entPhysicalTable.filter_by_column('Class', "'powerSupply'")
        for entity in dict(ports.items() + pss.items()).values():
            parents = self.get_parents(entity)
            for p in range(len(parents)-1, 0, -1):
                parent_index = int(parents[p]['suffix'])
                index = int(parents[p-1]['suffix'])
                if not hierarchy.get(parent_index):
                    hierarchy[parent_index] = []
                hierarchy[parent_index].append(index)
        for parent, childrenin in hierarchy.items():
            hierarchy[parent] = list(set(childrenin))
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

    #
    # Auxiliary public methods.
    #

    def get_parents(self, entity, *_parents):
        """
        :param entity: entity to return parents for.
        :return: autoload parents, up to the chassis, of the requested entity.
        """

        parents_l = list(_parents)
        parents_l.append(entity)
        if entity['entPhysicalClass'] == "'chassis'":
            return parents_l
        else:
            return self.get_parents(self.get_parent(entity), *parents_l)

    def get_parent(self, entity):
        """
        :param entity: entity to return parent for.
        :return: autoload parent of the requested entity.
        """

        parent = self.entPhysicalTable[int(entity['entPhysicalContainedIn'])]
        if parent['entPhysicalClass'] in self.autolad_parents[entity['entPhysicalClass']]:
            return parent
        else:
            return self.get_parent(parent)
