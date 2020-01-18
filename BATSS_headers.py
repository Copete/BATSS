from astropy import units as u
from astropy.time import Time
from astropy.io import fits
from astropy.table import Table
from astropy import wcs

# BATSS imports
import BATSS_utils
from BATSS_classes import BATSS_dir

def BATSS_gtihdr(
        gti,    #Dict or Table with 'start' and 'stop' fields [sec]
        extname = 'GTI',
        comment = 'extension name'
        ):

    # Check input
    if isinstance(gti, dict):
        start, stop = [], []
        for key, value in gti.items():
            if str(key).upper() == 'START':
                assert len(start) == 0
                start = value if isinstance(value, list) else [value]
            if str(key).upper() == 'STOP':
                assert len(stop) == 0
                stop = value if isinstance(value, list) else [value]
        gti_Table = Table({'START':start * u.s, 'STOP':stop * u.s}, names=('START','STOP'))
        del start, stop
    elif isinstance(gti, Table):
        gti_Table = gti
    else:
        raise TypeError('gti must be dict or astropy Table')

    # Make header
    gtihdr = fits.BinTableHDU(gti_Table, name=extname).header
    gtihdr.comments['EXTNAME'] = comment
    [gtihdr.add_comment(s, before='TTYPE1') for s in ['','  *** Time column fields ***','']]
    gtihdr.comments['TTYPE1'] = 'GTI start time'
    gtihdr['TFORM1'] = ('D', 'Data format of field: 8-byte DOUBLE')
    gtihdr.comments['TUNIT1'] = 'Units for START column'
    gtihdr.comments['TTYPE2'] = 'GTI stop time'
    gtihdr['TFORM2'] = ('D', 'Data format of field: 8-byte DOUBLE')
    gtihdr.comments['TUNIT2'] = 'Units for STOP column'
    [gtihdr.add_comment(s, after=-1) for s in ['','  *** End of table fields ***','']]
    gtihdr.extend([
        ('HDUCLASS', 'OGIP'     , 'Format conforms to OGIP standards'),
        ('HDUCLAS1', 'GTI'      , 'Good Time Interval'),
        ('HDUCLAS2', 'STANDARD' , 'Standard GTI'),
        ('TIMESYS' , 'TT'       , 'Time system'),
        ('MJDREFI' , 51910.     , 'Reference MJD Integer part'), #f='F6.0'
        ('MJDREFF' , 0.00074287037, 'Reference MJD fractional'), #f='F13.11'
        ('TIMEREF' , 'LOCAL'    , 'Time reference (barycenter/local)'),
        ('TASSIGN' , 'SATELLITE', 'Time assigned by clock'),
        ('TIMEUNIT', 's'        , 'Time unit'),
        ('TSTART'  , min(gti_Table['START']), '(MET) Start time'),
        ('TSTOP'   , max(gti_Table['STOP']),  '(MET) Stop time')],
        bottom=True, update=True)
    date_obs, utcf_start = BATSS_utils.met2Time(gtihdr['TSTART'], utcf=True)
    date_end = BATSS_utils.met2Time(gtihdr['TSTOP'], utcf=True)[0]
    gtihdr.extend([
        ('DATE-OBS', date_obs.isot, 'Date and time of observation start'),
        ('DATE-END', date_end.isot, 'Date and time of observation stop'),
        ('CLOCKAPP', 'F'        , 'default'),
        ('UTCFINIT', utcf_start, '[s] UTCF at TSTART'), #f='F8.5'
        ('TELAPSE' , gtihdr['TSTOP']-gtihdr['TSTART'], 'TSTOP - TSTART'),
        ('DEADC'   , 1.         , 'Dead time correction')], #f='F2.0'
        bottom=True, update=True)
    # Default for ONTIME, LIVETIME, EXPOSURE
    time = sum(gti_Table['STOP']-gti_Table['START'])
    gtihdr.extend([
        ('ONTIME'  , time, 'Time on target'), #f='F13.3'
        ('LIVETIME', time * gtihdr['DEADC'], 'Ontime multiplied by DEADC'), #f='F13.3'
        ('EXPOSURE', time * gtihdr['DEADC'], 'Total exposure, with all known correction'), #f='F13.3'
        ('TELESCOP', 'SWIFT'    , 'Telescope (mission) name'),
        ('INSTRUME', 'BAT'      , 'Instrument name'),
        ('OBS_ID'  , '00000000000', 'Observation number ID'),
        ('TARG_ID' , 0          , 'Target_ID value'),
        ('SEG_NUM' , 0          , 'Observation segment value'),
        ('EQUINOX' , 2000.      , 'default'), #f='F5.0'
        ('RADESYS' , 'FK5'      , 'default'),
        ('ORIGIN'  , 'HARVARD'  , 'Source of FITS file'),
        ('CREATOR' , 'BATSS_gtihdr', 'Program that created this FITS header'),
        ('DATE'    , Time.now().isot,
            'file creation date (UT)')],
        bottom=True, update=True)
    [gtihdr.add_comment(s, after=-1) for s in ['','  *** End of BATSS_gtihdr output ***','']]

    return gtihdr

#---------------------------------------------------------------------------
# Modify header astrometry for standard BAT tangent plane projection images
# 08/16/18: Function created

def BAT_astrmod(
        header,      # Input image header of type Header
        ra = 0.,    # RA of reference pixel
        dec = 0.,   # Dec of reference pixel
        roll = 0.   # Roll angle of image
        ):
    '''
    Modify header astrometry for standard BAT tangent plane projection images
    '''

    # Check input parameters
    assert isinstance(header, fits.Header)

    # Get default TAN astrometry structure from default partial coding image
    imgfile_def = BAT_pcfile_def()
    hdr_def = fits.getheader(imgfile_def)

    # Modify ra, dec, roll
    hdr_def['CRVAL1'] = ra
    hdr_def['CRVAL2'] = dec
    hdr_def['CROTA2'] = -roll  # Correct orientation

    # Extract WCS information and create modified FITS header
    wcs_mod = wcs.WCS(hdr_def)
    hdr_mod = wcs_mod.to_header()

    # Modify input header
    header.remove('RADECSYS', ignore_missing=True,
        remove_all=True)  # Remove deprecated keyword
    for key in header.keys():
        if key != 'HISTORY' and key != 'COMMENT':
            last_key = key
    header.update(hdr_mod)
    header.add_comment('----------------------------------'
        ' Additional WCS keywords', after=last_key)

    return header
