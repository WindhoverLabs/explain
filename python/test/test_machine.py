"""
This suite should only be run if there is a database populated with the full
Airliner build.
"""

from explain.map import SymbolMap
from test import RequiresDatabase


class TestMachine(RequiresDatabase):
    def setUp(self):
        super(TestMachine, self).setUp()
        c = self.db.execute('SELECT id FROM symbols WHERE name="MACHINE"')
        if c.fetchone() is None:
            self.fail('Prerequisite symbol MACHINE not found.')

    def test_machine(self):
        machine = SymbolMap.from_name(self.db, 'MACHINE')
        self.assertIsInstance(
            machine, SymbolMap, 'MACHINE must be a SymbolMap.')
        # pprint(explain_symbol(machine))
