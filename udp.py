from socket import socket, AF_INET, SOCK_DGRAM
import logging

osc_logger = logging.getLogger('osc')


class UDP(object):
    def __init__(self, host, port):
        self.destination = (host, port)
        self.socket = socket(AF_INET, SOCK_DGRAM)

    def relay(self, packet):
        self.socket.sendto(packet, self.destination)
