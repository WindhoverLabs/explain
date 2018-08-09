import os
import sqlite3
from unittest import TestCase


database_path = os.path.join(os.path.dirname(__file__), '../db.sqlite')


class RequiresDatabase(TestCase):
    def setUp(self):
        # Verify prerequisites
        if not os.path.exists(database_path):
            self.fail('Prerequisite database does not exist.')
        self.db = sqlite3.connect(database_path)
