import logging
from serial import SerialException
from serial.threaded import Packetizer
slip_logger = logging.getLogger('slip')


class SLIP(Packetizer):
    END = 0o0300
    ESC = 0o0333
    ESC_END = 0o0334
    ESC_ESC = 0o0335
    TERMINATOR = chr(END)

    def __init__(self, *args, **kwargs):
        super(SLIP, self).__init__(*args, **kwargs)
        self.destination = None
        self.verbose = False
        slip_logger.info("Connected.")

    def connection_lost(self, exc):
        slip_logger.warn('Connection lost: {}'.format(exc))
        try:
            super(SLIP, self).connection_lost(exc)
        except SerialException:
            pass

    def handle_packet(self, packet):
        if len(packet) == 0:
            return  # ignore empty packets
        unstuffed = bytearray()
        escaped = False
        for byte in packet:
            if escaped:
                if byte == SLIP.ESC_END:
                    unstuffed.append(SLIP.END)
                elif byte == SLIP.ESC_ESC:
                    unstuffed.append(SLIP.ESC)
                else:
                    slip_logger.warn('ESC not followed by ESC_END or ESC_ESC')
                    unstuffed.append(byte)
                escaped = False
                continue
            if byte == SLIP.ESC:
                escaped = True
                continue
            unstuffed.append(byte)
        if self.destination is not None:
            self.destination.relay(unstuffed)
        if self.verbose:
            action = 'dropping' if self.destination is None else 'relaying'
            print '{} packet: {}'.format(action, unstuffed)
