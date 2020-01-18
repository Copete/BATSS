import os
import subprocess as subp
from astropy.time import Time

# BATSS imports
from BATSS_classes import BATSS_dir

def met2Time(met, utcf=False):
    '''
    Perform swifttime transformation
    to return Time object from given MET
    '''

    if not isinstance(met, list):
        met = [met]
        scalar_flag = True
    else:
        scalar_flag = False
    mjd = []
    utcf_value = []

    #TEMP
    for met0 in met:
        mjd.append(Time(51910. + met0/86400., format='mjd'))
        utcf_value.append(0.)

    #Skip for now!
    #for met0 in met:
    if False:
        command = ['swifttime', f'intime={met0:17.11f}', 'insystem=MET', 'informat=s', 'outsystem=UTC', 'outformat=m', 'chatter=3']
        res = subp.run(command, stdout=subp.PIPE, stderr=subp.PIPE)
        if res.stderr != b'':
            print(res.stderr.decode('utf-8'))
            raise
        else:
            w = res.stdout.find(b'Converted time:') + 15
            mjd.append(Time(float(res.stdout[w:w+res.stdout[w:].find(b'\n')]), format='mjd'))
            w = res.stdout.find(b'Spacecraft clock correction') + 27
            w += res.stdout[w:].find(b'(') + 1
            utcf_value.append(float(res.stdout[w:w+res.stdout[w:].find(b')')]))
            ### Check for clock offset errors
    if scalar_flag:
        mjd = mjd[0]
        utcf_value = utcf_value[0]

    if utcf:
        return mjd, utcf
    else:
        return mjd

#---------------------------------------------------------------------------
# Get default BAT partial coding map FITS file
# 01/17/20: Function created

def BAT_pcfile_def(): # No inputs
    '''
    Get default BAT partial coding map FITS file
    '''
    pcfile_def = BATSS_dir.root + 'pipeline/pcode_default.img'
    if not os.path.exists(pcfile_def):
        raise IOError('Default partial coding file does not exist ('
            +pcfile_def+')')
    print('Function BAT_pcfile_def accessed successfully!')
    return pcfile_def
