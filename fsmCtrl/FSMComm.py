#!/usr/bin/python
import serial
from serial.tools import list_ports
import struct as st
from fastcrc import crc32

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fsmCtrl')


# Communication variables
baud = 38400;
timeout = 0.8;

# Need to find out idVendor and idProduct
class FSM:
    def __init__(self, idVendor='1027', idProduct='24593'):
        """ This creates the serial connection to the FSM """

        self.idVendor = idVendor;
        self.idProduct = idProduct;

        self.port = self._determine_port();
        if self.port is None:
            raise ValueError('Could not determine port!')

#        self.port = '/dev/ttyUSB0'
        
        try:
            print("Trying to connect to serial port");
            self.fsmconnect = serial.Serial(self.port, baud, timeout=timeout);
        except (serial.SerialException,ValueError):
            raise ValueError('There was an error opening the port');
        logger.info("Opened the FSM port successfully.");


    def _determine_port(self):
        """ Determine the port from the USB idVendor and idProduct
        Stolen from: https://stackoverflow.com/a/38745584
        """
        port = None; # initialize port to None and see if it can be assigned
        device_list = list_ports.comports();
        for device in device_list:
            if (device.vid != None or device.pid != None):
                if ('{:04X}',format(device.vid) == self.idVendor and
                    '{:04X}',format(device.pid) == self.idProduct):
                    # test to see if first of the 4 USB ports
                    if (device.usb_interface_path[-1] == '0'):
                        print("got path 0");
                        port = device.device;
                        print(port)
        return port

        
    def setHV(self,va=0,vb=0,vc=0):
        """ This will create the command to write to the serial port and send it to the FSM """
        digA,digB,digC = convertVoltsToDac(va,vb,vc);

        packet_to_send = self.formatVoltageCommand(digA,digB,digC);
#        print(hex(packet_to_send));  # for diagnostics
        
        try:
            self.fsmconnect.write(packet_to_send);  # Need to uncomment to actually write to the port
            print("Writing to port...");
        except (serial.SerialException,ValueError):
            print("Can't write to the port");
        return;

    def formatVoltageCommand(self,va,vb,vc):
        packet = st.pack('<LHHLLL',0x1BADBABE,2,12,va,vb,vc);
        check = crc32.bzip2(packet);
#        print(hex(check));
        formatted_packet = st.pack('<LHHLLLLL',0x1BADBABE,2,12,va,vb,vc,check,0x0A0FADED);
        return formatted_packet

    def close(self):
        self.fsmconnect.close()


### Note: Is there a way to read the current voltages?  We might want to change a single axis
def convertVoltsToDac(volta=0,voltb=0,voltc=0):
    
    digValueA = round(volta/(4.096/2.0**24*60));
    digValueB = round(voltb/(4.096/2.0**24*60));
    digValueC = round(voltc/(4.096/2.0**24*60));
    return digValueA,digValueB,digValueC
