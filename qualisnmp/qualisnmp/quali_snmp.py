"""
This package contains classes and utility functions to work with SNMP in Quali shells.

This package assumes that its users are familiar with SNMP basics but are not necessarily
professionals. Thus the operations and terminology are not always by the book but reflects the
needs of Quali SNMP users.
"""

from collections import OrderedDict

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.error import PySnmpError
from pysnmp.smi import builder, view
from pysnmp.smi.rfc1902 import ObjectIdentity

cmd_gen = cmdgen.CommandGenerator()
mib_builder = builder.MibBuilder()
mib_viewer = view.MibViewController(mib_builder)


def load_mib(mib):
    """ Load MIB

    :param mib: MIB name (without any suffix).
    """
    mib_builder.loadModules(mib)


def filter_table(table, attribute, value):
    pass

# Load default MIBs.
for mib in ('SNMPv2-MIB', 'IF-MIB', 'ENTITY-MIB'):
    load_mib(mib)


class QualiSnmpError(PySnmpError):
    pass


class QualiMibTable(OrderedDict):
    """ Represents MIB table.

    Note that this class inherits from OrderedDict so all dict operations are supported.
    """

    def __init__(self, name, *args, **kwargs):
        """ Create ordered dictionary to hold the MIB table.

        MIB table representation:
        {index: {attribute: value, ...}...}

        :param name: MIB table name.
        """
        super(QualiMibTable, self).__init__(*args, **kwargs)
        self._name = name
        self._prefix = name[:-len('Table')]

    def get_rows(self, *indexes):
        """
        :param indexes: list of requested indexes.
        :return: a partial table containing only the requested rows.
        """
        return QualiMibTable(self._name, OrderedDict((i, v) for i, v in self.items() if
                                                     i in indexes))

    def get_columns(self, *names):
        """
        :param names: list of requested columns names.
        :return: a partial table containing only the requested columns.
        """
        names = [self._prefix + n for n in names]
        return QualiMibTable(self._name, OrderedDict((i, {n: v for n, v in values.items() if
                                                          n in names}) for
                                                     i, values in self.items()))

    def filter_by_column(self, name, *values):
        """
        :param name: column name.
        :param values: list of requested values.
        :return: a partial table containing only the rows that has one of the requested values in
            the requested column.
        """
        name = self._prefix + name
        return QualiMibTable(self._name, OrderedDict((i, _values) for i, _values in self.items() if
                                                     _values[name] in values))

    def sort_by_column(self, name):
        """
        :param name: column name.
        :return: the same table sorted by the value in the requested column.
        """
        column = self.get_columns(name)
        name = self._prefix + name
        return QualiMibTable(self._name, sorted(column.items(), key=lambda t: int(t[1][name])))


class QualiSnmp(object):
    """ A wrapper class around PySNMP.

    :todo: use pysnmp.hlapi, do we really need to import symbols? see
        pysnmp.sourceforge.net/examples/hlapi/asyncore/sync/manager/cmdgen/table-operations.html
    """

    var_binds = ()
    """ raw output from PySNMP command. """

    def __init__(self, ip, port=161, community='private', v3_user=None):
        """ Initialize SNMP environment .

        :param ip: device IP.
        :param port: device SNMP port.
        :param community: device community string.
        """
        super(QualiSnmp, self).__init__()

        self.target = cmdgen.UdpTransportTarget((ip, port))

        if v3_user:
            self.security = v3_user
        else:
            self.security = cmdgen.CommunityData(community)

    def get(self, *oids):
        """ Get/Bulk get operation for scalars.

        :param oids: list of oids to get. oid can be full dotted OID or (MIB, OID name, [index]).
            For example, the OID to get sysContact can by any of the following:
            ('SNMPv2-MIB', 'sysContact', 0)
            ('SNMPv2-MIB', 'sysContact')
            '1.3.6.1.2.1.1.4.0'
            '1.3.6.1.2.1.1.4'
        :return: a dictionary of <oid, value>
        """

        object_identities = []
        for oid in oids:
            if type(oid) is list or type(oid) is tuple:
                oid_0 = list(oid)
                if len(oid_0) == 2:
                    oid_0.append(0)
                object_identities.append(ObjectIdentity(*oid_0))
            else:
                oid_0 = oid if oid.endswith('.0') else oid + '.0'
                object_identities.append(ObjectIdentity(oid_0))

        self._command(cmd_gen.getCmd, *object_identities)

        oid_2_value = OrderedDict()
        for var_bind in self.var_binds:
            modName, mibName, suffix = mib_viewer.getNodeLocation(var_bind[0])
            oid_2_value[mibName] = var_bind[1].prettyPrint()

        return oid_2_value

    def next(self, oid):
        """ Get next for a scalar.

        :param oid: oid to getnext.
        :return: a pair of (next oid, value)
        """

        self._command(cmd_gen.nextCmd, ObjectIdentity(*oid),)

        var_bind = self.var_binds[0][0]
        modName, mibName, suffix = mib_viewer.getNodeLocation(var_bind[0])
        value = var_bind[1].prettyPrint()

        return (mibName, value)

    def walk(self, oid, *indexes):
        """ Walk through the given table OID.

        :param oid: oid of the table to walk through.
        :param indices: only walk through the requested indices.
        :return: a dictionary of <index, <attribute, value>>
        """

        self._command(cmd_gen.nextCmd, ObjectIdentity(*oid))

        oid_2_value = QualiMibTable(oid[1])
        for var_bind in self.var_binds:
            modName, mibName, suffix = mib_viewer.getNodeLocation(var_bind[0][0])
            # We want table index to be numeric if possible.
            if str(suffix).isdigit():
                # Single index like 1, 2, 3... - treat as int
                index = int(str(suffix))
            elif str(suffix).replace('.', '', 1).isdigit():
                # Double index like 1.1, 1.2, 2.1... - treat as float
                index = float(str(suffix))
            else:
                # Triple or more index (like IPv4 in IP-Table) - treat as str.
                index = str(suffix)
            if not oid_2_value.get(index):
                oid_2_value[index] = {}
            oid_2_value[index][mibName] = var_bind[0][1].prettyPrint()

        if indexes:
            oid_2_value = oid_2_value.get_rows(*indexes)

        return oid_2_value

    #
    # Private methods.
    #

    def _command(self, cmd, *oids):
        error_indication, error_status, error_index, self.var_binds = cmd(self.security,
                                                                          self.target, *oids)

        # Check for errors
        if error_indication:
            raise PySnmpError(error_indication)
        if error_status:
            raise PySnmpError(error_status)
