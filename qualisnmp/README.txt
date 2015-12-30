qualisnmnp package is set of SNMP based tools for Quali shells developers.
 
This package assumes that its users are familiar with SNMP basics but are not necessarily
professionals. Thus the operations and terminology are not always by the book but reflects the
needs of Quali SNMP users.

1. qualisnmp

Support for SNMP tables and operations.

2. Autoload

In order to implement autoload functionality a device  must return its hierarchy and some
attributes for each entity in the hierarchy.
Device hierarchy is saved in the ENTITY-MIB under entPhysicalTable. However, it is not enough to
retrieve the hierarchy as described in the entPhysicalContainedIn entry. Autoload does not care
about some entities (for example, sensors) and does not care for some hierarchies (for example
containers). Autoload cares for the following hierarchy:

chassis
	+-module
		+-submodule
			+--port
		+-port
	+port
	+power supply

In the context of this module we define the following terms:
Autolod entity - an entity that should be represented in Quali RM - chassis, module, submodule,
port and power supply.
Autolod hierarchy - all autoload entities and their hierarchy as described above.
Autoload parent - the parent of the autoload entity in the autoload hierarchy.
