from docker_status import check
import json
import unittest


class TestStatus(unittest.TestCase):

    def setUp(self):
        self.index_status_1 = json.dumps({
            'redis': {
                'status': 'failure',
                'message': "ERR wrong number of arguments for 'set' command"},
            'host': {'hostname': 'index-default-www-1'},
            'redis-cache': {'status': 'ok'},
            'elasticsearch': {'status': 'ok'},
            'database': {'status': 'ok'}}, sort_keys=True, skipkeys=True)

    def test_status_normalization(self):
        index_status_1 = json.dumps({
            'services': ['database', 'elasticsearch', 'redis', 'redis-cache'],
            'failures': {
                'redis': "ERR wrong number of arguments for 'set' command"}
        }, sort_keys=True, skipkeys=True)
        normalized_index_status_1 = json.dumps(
            check.normalize_status('index', json.loads(self.index_status_1)),
            sort_keys=True, skipkeys=True)
        self.assertEqual(index_status_1, normalized_index_status_1)


if __name__ == '__main__':
    unittest.main()
