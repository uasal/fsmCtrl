from time import sleep
from time import time
import numpy as np

from magpyx.utils import ImageStream
#from magpyx.dm import dmutils
#from scoobpy.utils import get_kilo_map_mask

from .FSMComm import FSM

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fsmCtrl')

def run_FSM(shmim_name='fsm02disp', vref=4.096, nbits=24, vmult=60):
    '''
    Open FSM connection and await commands via shared memory image
    '''

    # ---- Setup ----
    shmim = ImageStream(shmim_name)
    logger.info(f'Connected to shared memory image {shmim_name}.')

    if shmim.semindex is None:
        shmim.semindex = shmim.getsemwaitindex(2)
        logger.info(f'Got semaphore index {shmim.semindex}.')

    logger.info('Opening FSM connection')
    fsmhandle = FSM()

    logger.info('Ready for commands. Ctrl+c to exit.')

    i = 0
    try:
        while True:
            # wait on a new command
            shmim.semwait(shmim.semindex)

            # get command (in Volts)
            # There are 3 voltages
            ### Help - how do we grab from shared memory??
            axis3volts = shmim.grab_latest()

            # convert to DAC value
            axis3volts_dac = axis3volts / (vref/2**nbits*vmult)

            # clip to maximum DAC value
            axis3volts_clipped = np.clip(axis3volts_dac , 0, 2**nbits - 1)

            # send clipped 2D array
            logger.info('Sending command!')
            t0 = time()
            send_array(fsmhandle, axis3volts_clipped)
            t1 = time()
            logger.info(f'{i}: Took {t1-t0} seconds')
            i += 1

    except KeyboardInterrupt: # this is broken, as always
        pass

    logger.info('Zeroing out all actuators')
    ### Help Again, how does share memory image work?  There should be 3 axes.
    ### Help Will hard code now until Kyle can give me guidance
    ### send_array(fsmhandle, np.zeros(shmim.shape))
    send_array(fsmhandle, np.zeros(3))
    sleep(1)

    logger.info('Closing FSM connection')
    fsmhandle.close()
    logger.info(f'Closing shared memory image {shmim_name}')
    shmim.close()

def console_run_FSM():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('--shmim', '-s', type=str, default='fsm02disp', help='Shared memory image to watch for commands. Default: fsm01disp')
    parser.add_argument('--vref','-v', type=float, default=4.096,  help='Reference voltage for the FSM DACs. Default: 4.096 V')
    parser.add_argument('--bits','-b', type=int, default=24,  help='Bit depth of FSM electronics. Default: 24')
    parser.add_argument('---mult','-m', type=int, default=60, help='Reference Voltage multiplier.  Default: 60')
    args = parser.parse_args()

    run_FSM(shmim_name=args.shmim, vref=args.vmax, nbits=args.bits, vmult=args.mult)


def send_array(fsm, arr):
    '''
    Send a positioning command to the FSM.  All three voltages are sent according to position requirement
    '''
    uiarr = arr.astype(np.uint32) # need at least 24 bits
    fsm.setHV(uiarr[0],uiarr,[1],uiarr[3])
