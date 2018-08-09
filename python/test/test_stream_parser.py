import os

from explain import stream_parser
from test import RequiresDatabase


TEST_FILE = os.path.join(os.path.dirname(__file__), 'flight_truncate.tlm')


class TestStreamParser(RequiresDatabase):
    def setUp(self):
        super(TestStreamParser, self).setUp()
        if not os.path.exists(TEST_FILE):
            self.fail('Simple telemetry file not found.')

    def test_stream_parser(self):
        with open(TEST_FILE, 'rb') as fp:
            parser = stream_parser.AirlinerStreamParser(
                self.db, fp, 'DS_FileHeader_t')
            for symbol in parser.parse():
                print(symbol)
