"""
Simple client server unit test
"""

import logging
import threading
import unittest

from context import lab_logging
from lab1.clientserver import Client
from lab1.phone_server import Server

lab_logging.setup(stream_level=logging.INFO)


class TestEchoService(unittest.TestCase):
    """The test"""
    _server = Server()  # create single server in class variable
    _server_thread = threading.Thread(target=_server.serve)  # define thread for running server

    @classmethod
    def setUpClass(cls):
        cls._server_thread.start()  # start server loop in a thread (called only once)

    def setUp(self):
        super().setUp()
        self.client = Client()  # create new client for each test

    def test_get(self):  # each test_* function is a test
        """Test simple call"""
        msg = self.client.get("John Smith")
        self.assertEqual(msg, "[('John Smith', '0721552211')]")

    def test_get_all(self):  # each test_* function is a test
        """Test simple call"""
        msg = self.client.get_all()
        self.assertEqual(msg,
                         "[('John Smith', '0721552211'), ('Caroline Smith', '0721552212'), ('Gordon Harper', '0721552213'), ('Piet Edwards', '0721552214'), ('Frida Frikadelle', '0721552215')]")

    def test_no_hit(self):
        msg = self.client.get("Karl Lagerfeld")
        self.assertEqual(msg,
                         "[]")

    def tearDown(self):
        self.client.close()  # terminate client after each test

    @classmethod
    def tearDownClass(cls):
        cls._server._serving = False  # break out of server loop. pylint: disable=protected-access
        cls._server_thread.join()  # wait for server thread to terminate


if __name__ == '__main__':
    unittest.main()
