#01/26/18
#Run imaging and detection for BAT pointings before and after a given slew,
#   for given sky coordinates
#   Adapted from IDL routine batss_pointing_detect.pro

import os, glob # For file search/manipulation
from datetime import datetime, timedelta
from astropy import units as u
from astropy.coordinates import SkyCoord
#from astropy.time import Time
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

        ##Time object with slew date
        #slew_date = Time('20'+slew_id0[:2]+'-'+slew_id0[2:4]+'-'+slew_id0[4:6])
        slew_date = datetime(int('20'+slew_id0[:2]), int(slew_id0[2:4]), int(slew_id0[4:6]))
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
        flag_realtime = False # Archival by default (condition for  realtime?)
        fitsfile = slew.fitsfile_realtime if flag_realtime else slew.fitsfile
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
        queuefile = slew.queuefile_realtime if flag_realtime else slew.queuefile

        with fits.open(queuefile) as queue_hdul:
            w = np.array([hdu.name == 'SLEW_'+slew_id0 for hdu in queue_hdul]).nonzero()[0]
        assert len(w) == 1

        ## Beginning of preceding pointing
        if w == 1:
            # Get slew from previous day
            date_pre = slew_date - timedelta(days=1)
            queuefile_pre = root+'products/'+ '{:04}_{:02}'.format(date_pre.year, date_pre.month)+ '/queue'+('_realtime' if flag_realtime else '')+ '/queue_'+'{:02}{:02}{:02}'.format(date_pre.year % 100, date_pre.month, date_pre.day)+'_slew.fits'
            try:
                with fits.open(queuefile_pre) as queue_pre_hdul:
                    wpre = len(queue_pre_hdul)
                    gti_pre_sod = -86400
            except OSError:
                print('File not found: '+queuefile_pre)
        else:
            queuefile_pre = queuefile
            queue_pre_hdul = queue_hdul
            wpre = w-1
        slew_id_pre = queue_pre_hdul[5:]  ## Open queue_pre again?
        gti_pre['start'] = fits.getval(queuefile_pre, 'END_SLEW', ext=wpre)
        gti_pre_sod['start'] += int(slew_id_pre[7:9])*3600 + int(slew_id_pre[10:12])*60 + int(slew_id_pre[13:15]) + int(slew_id_pre[17:20]) ## Check!
        ## End of following pointing
        if w == len(queue_hdul):
            # Get slew from following day
            date_pre = slew_date + timedelta(days=1)
            queuefile_pos = root+'products/'+ '{:04}_{:02}'.format(date_pos.year, date_pos.month)+ '/queue'+('_realtime' if flag_realtime else '')+ '/queue_'+'{:02}{:02}{:02}'.format(date_pos.year % 100, date_pos.month, date_pos.day)+'_slew.fits'
            try:
                with fits.open(queuefile_pos) as queue_pos_hdul:
                    wpos = len(queue_pos_hdul)
                    gti_pos_sod = 86400
            except OSError:
                print('File not found: '+queuefile_pos)
        else:
            queuefile_pos = queuefile
            queue_pos_hdul = queue_hdul
            wpos = w+1
        slew_id_pos = queue_pos_hdul[5:]  ## Open queue_pos again?
        gti_pos['stop'] = fits.getval(queuefile_pos, 'BEG_SLEW', ext=wpos)
        gti_pos_sod['stop'] += int(slew_id_pos[7:9])*3600 + int(slew_id_pos[10:12])*60 + int(slew_id_pos[13:15]) + int(slew_id_pos[17:20]) ## Check!
        # Read AFST files for previous, current and following days
        ### LATER
        ### build array "point"

        # Get Observation IDs for preceding and following pointings
        dt_pre = point['stop'].clip(max=gti_pre_sod['stop']) - point['start'].clip(min=gti_pos_sod['start'])
        upre = np.argmax(dt_pre)
        dt_pre = dt_pre[upre]
        assert dt_pre > 0
        obs_id_pre = point[upre]['obs_id']
        yymmdd_pre = point[upre]['yymmdd']
        dt_pos = point['stop'].clip(max=gti_pos_sod['stop']) - point['start'].clip(min=gti_pos_sod['start'])
        upos = np.argmax(dt_pos)
        dt_pos = dt_pos[upos]
        assert dt_pos > 0
        obs_id_pos = point[upos].obs_id
        yymmdd_pos = point[upos].yymmdd
        # Save GTI files for preceding and following pointings
        ## LATER

        # Perform BATSURVEY analysis on preceding and following pointings
        for o in [0,1]:
            print('{} {:%c}'.format(150*'=',datetime.now()))
            if o == 0:
                print('PRECEDING POINTING. ',end='')
                ## PRINT TO FILE!
                prefix = 'pre'
                gtifile = gtifile_pre
                obs_id = obs_id_pre
                yymmdd_point = yymmdd_pre
            else:
                print('FOLLOWING POINTING. ',end='')
                ## PRINT TO FILE!
                prefix = 'pos'
                gtifile = gtifile_pos
                obs_id = obs_id_pos
                yymmdd_point = yymmdd_pos
            yyyy_mm_point = '20'+yymmdd_point[:2]+'_'+yymmdd_point[2:4]
            print('Observation ID: '+obs_id)
            ## PRINT TO FILE!
            # Get coding fraction of source from attitude data
            gti = fits.getdata(gtifile,1)
            w = ((att['time'] > gti['start']) & (att['time'] < gti['stop'])).nonzero()[0]
            assert len(w) > 0
            w0 = (att[w]['flags'] == flag_settled).nonzero()[0]
            assert len(w0) > 0
            w = w[w0]
            w0 = (att[w]['obs_id'] == obs_id)
            assert len(w0) > 0
            w = w[w0]
            w0 = w[len(w)//2]
            RA0 = att[w0]['pointing'][0]
            Dec0 = att[w0]['pointing'][1]
            roll0 = att[w0]['pointing'][2]
            ## MODIFY PCHDR ASTROMETRY!
            ## x,y are coordinates of RA, Dec
            pcodefr0 = 100 * pcmap[x,y]
            print(f'Source coding fraction: {pcodefr0:6.2f}%. ',end='')
            ## PRINT TO FILE!
            if pcodefr0 == 0:
                print('Pointing skipped')
                ## PRINT TO FILE!
                continue
            print('Downloading pointing data...')
            ## PRINT TO FILE!
            ## EXECUTE SHELL COMMAND!!!

            # Loop over DPH and SNAPSHOT imaging
            datadir_in = obsdir
            for flag_dph in [0,1]:
                datadir_out = obsdir+'results_'+('_dph' if flag_dph else '')+'/'
                # BATSURVEY command
                ## EXECUTE BATSURVEY SHELL COMMAND!!!
                # Get output catalogs
                catalog = []
                catfile_out = glob.glob(datadir_out+'point_*/point_*_2.cat')
                if len(catfile_out) > 0:
                    print(('DPH' if flag_dph else 'SNAPSHOT')+' catalogs found:',len(catfile_out))
                else:
                    print('Waring: No '+('DPH' if flag_dph else 'SNAPSHOT')+' catalogs found. Skipping')
                for catfile_out0 in catfile_out:
                    t_ss = os.path.basename(catfile_out0).split('_')[1]
                    print(f' {t_ss[:4]}-{t_ss[4:7]}-{t_ss[7:9]}:{t_ss[9:11]}...', end='')
                    cat = fits.getdata(catfile_out0,1)
                    cat['name'] = cat['name'].strip()
                    cat['rate'] /= 0.16 #[cts/cm2/sec]
                    cat['cent_rate'] /= 0.16
                    cat['rate_err'] /= 0.16
                    cat['bkg_var'] /= 0.16
                    w = (cat.name == coord_str).nonzero()[0]
                    if len(w) > 0:
                        pass ##TEMP
                        ## ADD CAT TO CATALOG!
                # SAVE CATALOG FILE!
                n_det = len(catalog)
                ## PRINT TO FILE!!!
