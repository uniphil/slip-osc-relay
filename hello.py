from serial import Serial
from serial.tools import list_ports
from serial.threaded import Packetizer, ReaderThread
from Queue import Queue
from socket import socket, AF_INET, SOCK_DGRAM
# from time import sleep
import logging
logging.basicConfig(level=logging.INFO)
slip_logger = logging.getLogger('slip')


class SLIP(Packetizer):
    END = 0o0300
    ESC = 0o0333
    ESC_END = 0o0334
    ESC_ESC = 0o0335
    TERMINATOR = chr(END)

    def __init__(self, *args, **kwargs):
        super(SLIP, self).__init__(*args, **kwargs)
        self.packets = Queue()

    def __iter__(self):
        return iter(self.packets.get, None)

    def handle_packet(self, packet):
        if len(packet) == 0:
            return  # ignore empty packets
        out = bytearray()
        escaped = False
        for byte in packet:
            if escaped:
                if byte == SLIP.ESC_END:
                    out.append(SLIP.END)
                elif byte == SLIP.ESC_ESC:
                    out.append(SLIP.ESC)
                else:
                    slip_logger.warn('ESC not followed by ESC_END or ESC_ESC')
                    out.append(byte)
                escaped = False
                continue
            if byte == SLIP.ESC:
                escaped = True
                continue
            out.append(byte)
        self.packets.put(out)


def config():
    import argparse
    parser = argparse.ArgumentParser(
        description='Relay SLIP-framed packets from serial port to UDP')
    parser.add_argument(
        '--serial-baud', type=int, default=19200,
        help='Serial baud rate (default 19200)')
    parser.add_argument(
        '--serial-port',
        help='Serial port (default: autodetect)')
    parser.add_argument(
        '--osc-host', default='0.0.0.0',
        help='OSC UDP host (default 0.0.0.0)')
    parser.add_argument(
        '--osc-port', type=int, default=8010,
        help='OSC UDP port (default 8010)')

    args = parser.parse_args()

    if args.serial_baud < 1:
        parser.error('SERIAL_BAUD must be a positive integer')

    if args.osc_port < 1:
        parser.error('OSC_PORT must be greater than zero')

    serial_port = args.serial_port
    if serial_port is None:
        maybes = list(list_ports.grep('usb'))
        if len(maybes) == 0:
            parser.error('Could not autodetect serial port, please specify with --serial-port')
        if len(maybes) > 1:
            parser.error('Detected multiple serial port candidates, please specify with --serial-port. Likely candidates:\n{}\n'.format(
                '\n'.join(map(lambda m: '{}\t{}\t{}'.format(m.device, m.description, m.manufacturer), maybes))))
        serial_port = maybes[0].device

    return args.serial_baud, serial_port, args.osc_host, args.osc_port


if __name__ == '__main__':
    serial_baud, serial_port, osc_host, osc_port = config()

    ser = Serial(serial_port, serial_baud)
    sock = socket(AF_INET, SOCK_DGRAM)
    with ReaderThread(ser, SLIP) as packets:
        for packet in packets:
            # print packet
            sock.sendto(packet, (osc_host, osc_port))

    # sleep(10)
