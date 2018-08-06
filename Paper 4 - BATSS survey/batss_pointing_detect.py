#01/26/18
#Run imaging and detection for BAT pointings before and after a given slew,
#   for given sky coordinates
#   Adapted from IDL routine batss_pointing_detect.pro

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.table import Table

def batss_pointing_detect(slew_id, #should be BATSS_slew object?
ra,dec,eband):
    '''
    Run imaging and detection for BAT pointings befor and after a given slew,
    for given sky coordinates and energy band
    '''

    #Check input parameters

    for s,slew_id0 in enumerate(slew_id):
        pos = SkyCoord(ra[s], dec[s], unit='deg')
        eband_str = str(eband)

        coord_str = 'J'+pos.ra.to_string(unit='hour',pad=True,sep='',fields=2) +(10*pos.dec).to_string(pad=True,sep='',fields=1,alwayssign=True)

        print(150*'=')
        print('SLEW ID: ',slew_id0)
        print('Coordinates to search (J2000): ',pos.to_string('hmsdms'))
        print('Energy band: '+eband_str+' ('+eband+'keV)') #Revise

        #output text file
        txtfile = slew_id0+'.txt'
        f = open(txtfile, 'w')
        f.write('SLEW ID: '+slew_id0+'\n')
        f.write('Coordinates to search (J2000): '+pos.to_string('hmsdms')+'\n')
        f.write('Energy band: '+eband_str+' ('+eband+'keV)'+'\n') #Revise

        #Input catalog file
        catfile_in = 'batss.in.cat'
        #INTRODUCE ERR_RAD COLUMN, AND MAKE SURE IT IS TRANSFERRED TO OUTPUT CATALOG!!!
        #--CATNUM: Source number within catalog
        #--NAME:   Source name
        #-- RA_CAT/GLON_CAT: Catalogued source longitude
        #--DEC_CAT/GLAT_CAT: Catalogued source latitude
        #-- RA_OBJ/GLON_OBJ: Source longitude (to be modified upon detection)
        #--DEC_OBJ/GLAT_OBJ: Source latitude  (to be modified upon detection)

        catalog = Table({'catnum':[0], 'name':[coord_str],
            'RA_OBJ':[pos.ra.deg], 'DEC_OBJ':[pos.dec.deg],
            'RA_CAT':[pos.ra.deg], 'DEC_CAT':[pos.dec.deg]})
            #'err_rad':8/60
        cat = fits.BinTableHDU(catalog)
        cat.header.set('HDUNAME', 'BAT_CATALOG', ' Name of extension')
        cat.header.set('HDUCLASS', 'CATALOG', ' Source catalog')
        cat.header.set('TNULL1',      -1, ' data null value', after='TFORM1')
        cat.header.set('TUNIT3',   'deg', ' physical unit of field', after='TFORM3')
        cat.header.set('TDISP3', 'F10.4', ' Column display format',  after=None) #'TNULL3')
        cat.header.set('TUNIT4',   'deg', ' physical unit of field', after='TFORM4')
        cat.header.set('TDISP4', 'F10.4', ' Column display format',  after=None) #'TNULL4')
        cat.header.set('TUNIT5',   'deg', ' physical unit of field', after='TFORM5')
        cat.header.set('TDISP5', 'F10.4', ' Column display format',  after='TUNIT5')
        cat.header.set('TUNIT6',   'deg', ' physical unit of field', after='TFORM6')
        cat.header.set('TDISP6', 'F10.4', ' Column display format',  after='TUNIT6')
        print(repr(cat.header))

        # Get master FITS header for slew
        # Archival FITS file by default (condition for  realtime?)
        flag_realtime = False
        if flag_realtime:
            fitsfile = slew.fitsfile_realtime
        else fitsfile = slew.fitsfile
        header = fits.getheader(fitsfile)
        # Partial coding map
        pcmap, pchdr = fits.getdata(slew.pcfile, header=True)
        dims_pcmap = shape(pcmap)
        # Attitude file
        att = fits.getdata(slew.attfile, 1)
        flag_settled = 192 # (BINARY) FLAGS field for settled spacecraft

        # Get time windows for preceding and following pointings
        gti_pre = {'start':0, 'stop':header['BEG_SLEW']} #[MET]
        gti_pre_sod = {'start':0, 'stop':int(slew.id[7:9])*3600 + int(slew.id[10:12])*60 + int(slew.id[13:15])} #[SOD]
        gti_pos = {'start':header['END_SLEW'], 'stop':0} #[MET]
        gti_pos_sod = {'start':gti_pre_sod['stop'] + int(slew.id[17:20]), 'stop':0} ;[SOD]

        queuefile =








        f.close()
