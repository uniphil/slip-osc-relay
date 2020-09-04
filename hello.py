# -*- coding: utf-8 -*-
import logging
from serial import Serial, SerialException
from serial.tools import list_ports
from serial.threaded import ReaderThread
from slip import SLIP
from udp import UDP
from time import sleep

app_logger = logging.getLogger('app')


def connect_serial(port, baud):
    first_try = True
    while True:
        maybes = list(list_ports.grep('usb'))
        if len(maybes) == 0:
            if first_try:
                app_logger.warn('Connect serial device or use --serial-port')
                first_try = False
            sleep(0.1)
            continue
        break

    if len(maybes) > 1:
        app_logger.warn('Multiple USB serial devices found, using {}'.format(
            maybes[0].device))

    return Serial(maybes[0].device, baud)


def config():
    import argparse
    parser = argparse.ArgumentParser(
        description='Relay SLIP-framed packets from serial port to UDP')
    parser.add_argument(
        '--serial-baud', type=int, default=115200,
        help='Serial baud rate (default 115200)')
    parser.add_argument(
        '--serial-port',
        help='Serial port (default: autodetect)')
    parser.add_argument(
        '--osc-ip', default='0.0.0.0',
        help='OSC UDP IP (default 0.0.0.0)')
    parser.add_argument(
        '--osc-port', type=int, default=8010,
        help='OSC UDP port (default 8010)')
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='Verbose output: monitor SLIP packets')

    args = parser.parse_args()

    if args.serial_baud < 1:
        parser.error('SERIAL_BAUD must be a positive integer')

    if args.osc_port < 1:
        parser.error('OSC_PORT must be greater than zero')

    return args.serial_port, args.serial_baud, args.osc_ip, args.osc_port,\
        args.verbose


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serial_port, serial_baud, osc_ip, osc_port, verbose = config()

    while True:
        try:
            ser = connect_serial(serial_port, serial_baud)
        except SerialException as e:
            app_logger.warn('Could not connect to serial: {}'.format(e))
            continue
        destination = UDP(osc_ip, osc_port)
        try:
            reader = ReaderThread(ser, SLIP)
            reader.start()
            _, slip = reader.connect()
            app_logger.info('Relaying {} → {}'.format(
                ser.port, '{}:{}'.format(osc_ip, osc_port)))
            slip.destination = destination
            slip.verbose = verbose
            while reader.is_alive():
                sleep(0.1)
        except SerialException as e:
            app_logger.warn('Serial exception: {}'.format(e))
            app_logger.info('Will try to reconnect...')
            continue
