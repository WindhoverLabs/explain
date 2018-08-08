"""
This suite should only be run if there is a database populated with the full
Airliner build.
"""
import os
from pprint import pprint
import sqlite3
from unittest import TestCase

from explain import explain_symbol
from explain.map import SymbolMap

database_path = os.path.join(os.path.dirname(__file__), '../db.sqlite')


class TestMachine(TestCase):
    def setUp(self):
        # Verify prerequisites
        if not os.path.exists(database_path):
            self.fail('Prerequisite database does not exist.')
        self.db = sqlite3.connect(database_path)
        c = self.db.execute('SELECT id FROM symbols WHERE name="MACHINE"')
        if c.fetchone() is None:
            self.fail('Prerequisite symbol MACHINE not found.')

    def test_machine(self):
        machine = SymbolMap.from_name(self.db, 'MACHINE')
        self.assertIsNotNone(machine, 'MACHINE must be a SymbolMap.')
        pprint(explain_symbol(machine))
