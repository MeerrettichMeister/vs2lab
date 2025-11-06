import ast
import logging
import socket

import const_cs
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)  # init loging channels for the lab


# pylint: disable=logging-not-lazy, line-too-long

class Server:
    """ The server """
    _logger = logging.getLogger("vs2lab.lab1.clientserver.Server")
    _serving = True

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # prevents errors due to "addresses in use"
        self.sock.bind((const_cs.HOST, const_cs.PORT))
        self.sock.settimeout(3)  # time out in order not to block forever
        self._logger.info("Server bound to socket " + str(self.sock))
        self.database = {
            "John Smith": "0721552211",
            "Caroline Smith": "0721552212",
            "Gordon Harper": "0721552213",
            "Piet Edwards": "0721552214",
            "Frida Frikadelle": "0721552215",
        }

    def serve(self):
        """ Serve echo """
        self.sock.listen(1)
        while self._serving:  # as long as _serving (checked after connections or socket timeouts)
            try:
                # pylint: disable=unused-variable
                (connection, address) = self.sock.accept()  # returns new socket and address of client
                while True:  # forever
                    data = connection.recv(1024)  # receive data from client
                    if not data:
                        break  # stop if client stopped
                    # CODE
                    obj = ast.literal_eval(data.decode("utf-8"))
                    if obj["operation"] == "get":
                        name = obj["name"]
                        if self.database.get(name) is not None:
                            connection.send(str([(name,self.database[name])]).encode("utf-8"))
                            self._logger.info("Sent phone number for " + obj["name"])
                        else:
                            connection.send(str([]).encode("utf-8"))
                            self._logger.info("No person found, returning empty")
                    elif obj["operation"] == "getAll":
                        entries = []
                        for entry in self.database.keys():
                            entries.append((entry,self.database[entry]))
                        connection.send(str(entries).encode("utf-8"))
                        self._logger.info("Sent all entries")
                    else:
                        connection.send("Invalid operation".encode("utf-8"))
                        self._logger.info("Operation is not suported")

                connection.close()  # close the connection
            except socket.timeout:
                pass  # ignore timeouts
        self.sock.close()
        self._logger.info("Server down.")