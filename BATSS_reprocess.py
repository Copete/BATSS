# 09/11/18 First version

import os
import numpy as np
from datetime import datetime
from astropy.io import fits
from BATSS_classes import BATSS_eband, BATSS_dir, BATSS_observation, BATSS_slew

def BATSS_reprocess(
        obs_id,
        realtime=False,
        clobber=False,  # Reprocess only if data is missing
        indent=2 # Number of characters to indent by
        ):
    '''
    Modify necessary BATSS queue files to reprocess a given observation
    '''

    t0 = datetime.now()
    ind = indent * ' '
    status = 0
    print(ind+'*** BATSS_reprocess ***')

    # Check input parameters
    obs = BATSS_slew(obs_id)
    flag_realtime = True if realtime == True else False
    print(ind+f'Observation: {obs.type.upper()} {obs.id}')


    # Check for presence of observation FITS file
    fitsfile = obs.fitsfile_realtime if flag_realtime else obs.fitsfile
    if os.path.exists(fitsfile):
        print(ind+'Valid master FITS file found. ', end='')
        if not clobber:
            print('Observation NOT queued for reprocessing. Returning.')
            status = 1
            return status
    else:
        print(ind+'Warning: Valid master FITS file not found. ', end='')
    print('Queueing observation for reprocessing.')

    # Check queue file
    queuefile = obs.queuefile_realtime if flag_realtime else obs.queuefile
    print(ind+'Queue file: '+queuefile)
    if not os.path.exists(queuefile):
        raise IOError(f'Queue file not found for {obs.type} {obs.id}')
    try:
        with fits.open(queuefile, 'update') as queue_hdul:
            # Fix queue file (esp. order of cards PCOUNT, GCOUNT)
            queue_hdul.verify('silentfix')
            iobs = np.array([hdu.name == obs.type.upper()+'_'+obs.id
                for hdu in queue_hdul]).nonzero()[0]
        assert len(iobs) == 1
    except IOErrror:
        raise
    else:
        iobs = iobs[0]

    # Before queueing observation, check required downstream observations
    ## TO DO: do this for orbital and above!!!

    # Set queue file keywords for reprocessing
    with fits.open(queuefile, 'update') as queue_hdul:
        queue_hdul[iobs].header['PROCESSD'] = False
        queue_hdul[iobs].header['QREAD'] = False
        queue_hdul[0].header['PROCESSD'] = False
        queue_hdul[0].header['OPEN'] = True
    print(ind+'Queue file modified successfully')

    return status
