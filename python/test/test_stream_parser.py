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
            symbols = list(parser.parse())
            self.assertEqual(len(symbols), 17)
            distance_sensor_msg = list(filter(
                lambda s: s.name == 'PX4_DistanceSensorMsg_t', symbols))
            vehicle_status_msg = list(filter(
                lambda s: s.name == 'PX4_VehicleStatusMsg_t', symbols))
            self.assertEqual(len(distance_sensor_msg), 16)
            self.assertEqual(len(vehicle_status_msg), 1)
