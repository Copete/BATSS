#01/26/18
#Run imaging and detection for BAT pointings before and after a given slew,
#   for given sky coordinates
#   Adapted from IDL routine batss_pointing_detect.pro

import os, glob # For file search/manipulation
import numpy as np
from datetime import datetime, timedelta
import subprocess as subp
from astropy import units as u
from astropy.coordinates import SkyCoord
#from astropy.time import Time
from astropy.io import fits
from astropy.table import Table
from astropy import wcs
from bs4 import BeautifulSoup # For parsing HTML files

# To include BATSS directory in current path
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
from BATSS_classes import BATSS_eband, BATSS_dir, BATSS_observation, BATSS_slew
from BATSS_headers import BATSS_gtihdr, BAT_astrmod

from BATSS_utils import met2Time

def batss_pointing_detect(obs_id, #should be BATSS_slew object?
    ra, dec,    # Source RA/Dec
    eband_name, # Source energy band
    err_rad):   # Source error radius (arcmin, 90%)
    '''
    Run imaging and detection for BAT pointings before and after a given slew,
    for given sky coordinates and energy band
    '''

    #Check input parameters
    obs = []    # Initialize observation list
    if isinstance(obs_id, list):
        for obs_id0 in obs_id:
            obs.append(BATSS_slew(obs_id0))
    else:
        obs.append(BATSS_slew(obs_id))
    pos = SkyCoord(ra, dec, unit='deg')
    coord_str = ('J'+pos.ra.to_string(unit='hour',pad=True,sep='',fields=2)
        +(10*pos.dec).to_string(pad=True,sep='',fields=1,alwayssign=True))
    eband = BATSS_eband(eband_name)
    err_rad = err_rad * u.arcmin

    # Input/Output directories
    root = BATSS_dir.root
    dataroot = './data/'
    if not os.path.exists(dataroot):
        os.makedirs(dataroot)

    # Loop over BATSS observations
    for obs0 in obs:
        t0 = datetime.now()
        ##Time object with slew date
        #obs_date = Time('20'+obs0.id[:2]+'-'+obs0.id[2:4]+'-'+obs0.id[4:6])
        obs_date = datetime(int('20'+obs0.id[:2]), int(obs0.id[2:4]), int(obs0.id[4:6]))

        print(f'{70*"="} {datetime.now():%c}')
        print('BATSS Observation type and ID: ', obs0.type.upper(), obs0.id)
        print('Coordinates to search (J2000): ',pos.to_string('hmsdms'))
        print('Energy band: '+eband.name+' ('+eband.str_keV+')')

        # Output directories
        datadir = dataroot+obs0.type+'_'+obs0.id+'_'+coord_str+ '_'+eband.name+'/'
        if not os.path.exists(datadir):
            os.makedirs(datadir)
        tempdir = datadir+'temp/'
        if not os.path.exists(tempdir):
            os.makedirs(tempdir)
        # Initialize output txt file
        txtfile = datadir+obs0.type+'_'+obs0.id+'_'+coord_str+ '_'+eband.name+'.txt'
        f = open(txtfile, 'w')
        f.write(f'{70*"="} {datetime.now():%c}\n')
        f.write('BATSS Observation type and ID: '+obs0.type.upper()+' '+obs0.id+'\n')
        f.write('Coordinates to search (J2000): '+pos.to_string('hmsdms')+'\n')
        f.write('Energy band: '+eband.name+' ('+eband.str_keV+')'+'\n')
        f.close()

        #Input catalog file
        catfile_in = tempdir+'batss.in.cat'
        #  CATNUM: Source number within catalog
        #  NAME:   Source name
        #  RA_CAT/GLON_CAT: Catalogued source longitude
        #  DEC_CAT/GLAT_CAT: Catalogued source latitude
        #  RA_OBJ/GLON_OBJ: Source longitude (to be modified upon detection)
        #  DEC_OBJ/GLAT_OBJ: Source latitude  (to be modified upon detection)
        #  ERR_RAD_BATSS: BATSS error radius (90%, deg)
        cat_in_Table = Table(
            {'CATNUM':[0],
            'NAME':['BATSS_'+coord_str],
            'RA_OBJ':[pos.ra.value] * pos.ra.unit,
            'DEC_OBJ':[pos.dec.value] * pos.dec.unit,
            'RA_CAT':[pos.ra.value] * pos.ra.unit,
            'DEC_CAT':[pos.dec.value] * pos.ra.unit,
            'ERR_RAD_BATSS':[err_rad.to_value(u.deg)] * u.deg},
            names=('CATNUM','NAME','RA_OBJ','DEC_OBJ','RA_CAT','DEC_CAT',
                'ERR_RAD_BATSS')) #Specifies column order
        cat_in = fits.BinTableHDU(cat_in_Table, name='BAT_CATALOG')
        cat_in.header.set('HDUNAME', 'BAT_CATALOG', 'Name of extension',
            before='TTYPE1') #Necessary?
        cat_in.header.set('HDUCLASS', 'CATALOG', 'Source catalog',
            before='TTYPE1')
        cat_in.header.comments['TTYPE1'] = 'Source number within catalog'
        cat_in.header.set('TNULL1', -1, 'data null value', after='TFORM1')
        cat_in.header.comments['TTYPE2'] = 'Source name'
        cat_in.header.comments['TTYPE3'] = 'Detected source longitude'
        cat_in.header.comments['TUNIT3'] = 'physical unit of field'
        cat_in.header.set('TDISP3', 'F10.4', 'column display format',
            after='TUNIT3')
        cat_in.header.comments['TTYPE4'] = 'Detected source latitude'
        cat_in.header.comments['TUNIT4'] = 'physical unit of field'
        cat_in.header.set('TDISP4', 'F10.4', 'column display format',
            after='TUNIT4')
        cat_in.header.comments['TTYPE5'] = 'Catalogued source longitude'
        cat_in.header.comments['TUNIT5'] = 'physical unit of field'
        cat_in.header.set('TDISP5', 'F10.4', 'column display format',
            after='TUNIT5')
        cat_in.header.comments['TTYPE6'] = 'Catalogued source latitude'
        cat_in.header.comments['TUNIT6'] = 'physical unit of field'
        cat_in.header.set('TDISP6', 'F10.4', 'column display format',
            after='TUNIT6')
        cat_in.header.comments['TTYPE7'] = 'BATSS cat_in. error radius (90%)'
        cat_in.header.comments['TUNIT7'] = 'physical unit of field'
        cat_in.header.set('TDISP7', 'F6.4', 'column display format',
            after='TUNIT7')
        cat_in.writeto(catfile_in, overwrite=True)


        print(obs0.fitsfile)
        print(obs0.fitsfile_realtime)

        # Get master FITS header for slew (archival by default)
        if not os.path.exists(obs0.fitsfile):
            if not os.path.exists(obs0.fitsfile_realtime):
                raise IOError('Neither archival nor real-time files found'
                    f' for {obs0.type} {obs0.id}')
            else:
                flag_realtime = True
        else:
            flag_realtime = False
        fitsfile = obs0.fitsfile_realtime if flag_realtime else obs0.fitsfile
        try:
            header = fits.getheader(fitsfile)
        except IOError as err:
            raise IOError(err)
        except:
            print('Some other error! (fitsfile)')
        # Partial coding map
        pcfile = obs0.pcfile_realtime if flag_realtime else obs0.pcfile
        try:
            if not os.path.exists(pcfile):
                raise IOError('Partial coding file ('
                    +('realtime' if flag_realtime else 'archival')
                    +') does not exist')
            pcmap, pchdr = fits.getdata(pcfile, header=True)
        except IOError:
            raise
        except:
            print('Some other error! (pcfile)')
        else:
            dims_pcmap = np.shape(pcmap)
        # Attitude file
        attfile = obs0.attfile_realtime if flag_realtime else obs0.attfile
        try:
            if not os.path.exists(attfile):
                raise IOError('Attitude file ('+('realtime' if flag_realtime else 'archival')+') does not exist')
            att = fits.getdata(obs0.attfile, 1)
        except IOError:
            raise
        else:
            flag_settled = 192 # (binary) FLAGS field for settled spacecraft

        # Get time windows for preceding and following pointings
        obs_t0 = header['BEG_SLEW'] #[MET]
        gti_pre = {'start':0, 'stop':header['BEG_SLEW']} #[MET]
        gti_pre_sod = {'start':0, 'stop':int(obs0.id[7:9])*3600 + int(obs0.id[10:12])*60 + int(obs0.id[13:15])} #[SOD]
        gti_pos = {'start':header['END_SLEW'], 'stop':0} #[MET]
        gti_pos_sod = {'start':gti_pre_sod['stop'] + int(obs0.id[17:20]), 'stop':0} #[SOD]

        queuefile = obs0.queuefile_realtime if flag_realtime else obs0.queuefile
        try:
            with fits.open(queuefile) as queue_hdul:
                w = np.array([hdu.name == 'SLEW_'+obs0.id for hdu in queue_hdul]).nonzero()[0]
            assert len(w) == 1
        except IOError:
            raise
        else:
            w = w[0]

        # Beginning of preceding pointing
        if w == 1:
            # Get slew from previous day
            date_pre = obs_date - timedelta(days=1)
            queuefile_pre = root + f'products/{date_pre.year:04}_{date_pre.month:02}/queue{"_realtime" if flag_realtime else ""}/queue_{date_pre.year % 100:02}{date_pre.month:02}{date_pre.day:02}_{obs0.type}.fits'
            try:
                with fits.open(queuefile_pre) as queue_pre_hdul:
                    wpre = len(queue_pre_hdul)
                    gti_pre_sod['start'] = -86400
            except OSError:
                print('File not found: '+queuefile_pre)
                raise
        else:
            queuefile_pre = queuefile
            queue_pre_hdul = queue_hdul
            wpre = w-1
        slew_id_pre = queue_pre_hdul[wpre].name[5:]
        gti_pre['start'] = fits.getval(queuefile_pre, 'END_SLEW', ext=wpre)
        gti_pre_sod['start'] += int(slew_id_pre[7:9])*3600 + int(slew_id_pre[10:12])*60 + int(slew_id_pre[13:15]) + int(slew_id_pre[17:20])
        # End of following pointing
        if w == len(queue_hdul):
            # Get slew from following day
            date_pre = obs_date + timedelta(days=1)
            queuefile_pos = root + f'products/{date_pos.year:04}_{date_pos.month:02}/queue{"_realtime" if flag_realtime else ""}/queue_{date_pos.year % 100:02}{date_pos.month:02}{date_pos.day:02}_{obs0.type}.fits'
            try:
                with fits.open(queuefile_pos) as queue_pos_hdul:
                    wpos = len(queue_pos_hdul)
                    gti_pos_sod['stop'] = 86400
            except OSError:
                print('File not found: '+queuefile_pos)
                raise
        else:
            queuefile_pos = queuefile
            queue_pos_hdul = queue_hdul
            wpos = w+1
        slew_id_pos = queue_pos_hdul[wpos].name[5:]
        gti_pos['stop'] = fits.getval(queuefile_pos, 'BEG_SLEW', ext=wpos)
        gti_pos_sod['stop'] += (int(slew_id_pos[7:9])*3600 +
            int(slew_id_pos[10:12])*60 + int(slew_id_pos[13:15]))

        # Read AFST files for previous, current and following days
        afst_obs_id = []
        afst_yymmdd = []
        afst_start_sod = []
        afst_stop_sod = []
        for d in [-1,0,1]:
            date0 = obs_date + timedelta(days=d)
            yymmdd = f'{date0.year % 100:02}{date0.month:02}{date0.day:02}'
            afstfile = (root + f'products/{date0.year:04}_{date0.month:02}/'
                f'afst/afst_{date0.year % 100:02}{date0.month:02}'
                f'{date0.day:02}.html')
            try:
                with open(afstfile,'r') as f0:
                    afst_soup = BeautifulSoup(f0) #, 'lxml')
            except OSError:
                raise
            tr = afst_soup.find_all('tr')
            for tr0 in tr:
                try:
                    afst_class = tr0['class'][0]
                except KeyError:
                    continue
                if afst_class == 'header':
                    continue
                td0 = tr0.find_all('td')
                start0 = td0[0].get_text(strip=True)
                start_sod0 = (datetime(int(start0[:4]), int(start0[5:7]), int(start0[8:10])) - obs_date).days*86400 + int(start0[11:13])*3600 + int(start0[14:16])*60 + int(start0[17:19])
                stop0 = td0[1].get_text(strip=True)
                stop_sod0 = (datetime(int(stop0[:4]), int(stop0[5:7]), int(stop0[8:10])) - obs_date).days*86400 + int(stop0[11:13])*3600 + int(stop0[14:16])*60 + int(stop0[17:19])
                afst_obs_id.append(td0[2].a.text.zfill(8) + td0[3].a.text.zfill(3))
                afst_yymmdd.append(yymmdd)
                afst_start_sod.append(start_sod0)
                afst_stop_sod.append(stop_sod0)
        point = Table({'obs_id':afst_obs_id, 'yymmdd':afst_yymmdd, 'start_sod':afst_start_sod, 'stop_sod':afst_stop_sod})
        del afst_obs_id, afst_yymmdd, afst_start_sod, afst_stop_sod

        # Get Observation IDs for preceding and following pointings
        dt_pre = point['stop_sod'].clip(max=gti_pre_sod['stop']) - point['start_sod'].clip(min=gti_pre_sod['start'])
        upre = np.argmax(dt_pre)
        dt_pre = dt_pre[upre]
        assert dt_pre > 0
        obs_id_pre = point[upre]['obs_id']
        yymmdd_pre = point[upre]['yymmdd']
        dt_pos = point['stop_sod'].clip(max=gti_pos_sod['stop']) - point['start_sod'].clip(min=gti_pos_sod['start'])
        upos = np.argmax(dt_pos)
        dt_pos = dt_pos[upos]
        assert dt_pos > 0
        obs_id_pos = point[upos]['obs_id']
        yymmdd_pos = point[upos]['yymmdd']
        del point

        # Save GTI files for preceding and following pointings
        gtifile_pre = tempdir+obs0.type+'_'+obs0.id+'_pre.gti'
        gti_pre_Table = Table({'START':[gti_pre['start']] * u.s, 'STOP':[gti_pre['stop']] * u.s}, names=('START','STOP'))
        gtihdr_pre = BATSS_gtihdr(gti_pre_Table)
        hdu_pre = fits.BinTableHDU(gti_pre_Table, header=gtihdr_pre)
        hdu_pre.writeto(gtifile_pre, overwrite=True)
        gtifile_pos = tempdir+obs0.type+'_'+obs0.id+'_pos.gti'
        gti_pos_Table = Table({'START':[gti_pos['start']] * u.s, 'STOP':[gti_pos['stop']] * u.s}, names=('START','STOP'))
        gtihdr_pos = BATSS_gtihdr(gti_pos_Table)
        hdu_pos = fits.BinTableHDU(gti_pos_Table, header=gtihdr_pos)
        hdu_pos.writeto(gtifile_pos, overwrite=True)

        # Perform BATSURVEY analysis on preceding and following pointings
        obs0.src_name = 'BATSS '+coord_str # Include BATSS source name
        for flag_pre in [True, False]:
            print(f'{70*"="} {datetime.now():%c}')
            f = open(txtfile, 'a')
            if flag_pre:
                print('PRECEDING POINTING. ',end='')
                f.write(f'\n{95*"="}\nPRECEDING POINTING. ')
                prefix = 'pre'
                gtifile = gtifile_pre
                obs_id = obs_id_pre
                yymmdd_point = yymmdd_pre
            else:
                print('FOLLOWING POINTING. ',end='')
                f.write(f'\n{95*"="}\nFOLLOWING POINTING. ')
                prefix = 'pos'
                gtifile = gtifile_pos
                obs_id = obs_id_pos
                yymmdd_point = yymmdd_pos
            yyyy_mm_point = '20'+yymmdd_point[:2]+'_'+yymmdd_point[2:4]
            print(f'Observation ID: {obs_id}')
            f.write(f'Observation ID: {obs_id}\n')
            # Get coding fraction of source from attitude data
            gti = fits.getdata(gtifile,1)
            w = ((att['time'] >= gti['start'])
                & (att['time'] <= gti['stop'])).nonzero()[0]
            assert len(w) > 0
            #print(f'Attitude records found within GTI: {len(w)}')
            w0 = (att[w]['flags'] == flag_settled).nonzero()[0]
            assert len(w0) > 0
            w = w[w0]
            #print(f'Settled records: {len(w)}')
            w0 = (att[w]['obs_id'] == obs_id).nonzero()[0]
            if len(w0) == 0:
                str_out = ('WARNING: No settled attitude records found for'
                    f' Observation {obs_id}')
                print(str_out)
                f.write('\t'+str_out+'\n')
                obs_id0, obs_id0_pos = np.unique(att[w]['obs_id'],
                    return_inverse=True)
                obs_id0_cts = np.bincount(obs_id0_pos)
                imax = obs_id0_cts.argmax()
                str_out = (f'\tUsing most frequent Obs ID: {obs_id0[imax]}'
                    f' ({obs_id0_cts[imax]} records)')
                print(str_out)
                f.write(str_out+'\n')
                obs_id = obs_id0[imax]
                w0 = (obs_id0_pos == imax).nonzero()[0]
                assert len(w0) > 0
                del obs_id0, obs_id0_pos, obs_id0_cts, imax
            w = w[w0]
            w0 = w[len(w)//2]
            ra0 = att[w0]['pointing'][0]
            dec0 = att[w0]['pointing'][1]
            roll0 = att[w0]['pointing'][2]
            # Modify pchdr astrometry
            pchdr = BAT_astrmod(pchdr, ra=ra0, dec=dec0, roll=roll0)
            #fits.PrimaryHDU(pcmap, pchdr).writeto(datadir+'test_pchdr_'
            #    +prefix+'.fits', overwrite=True) #TEMP
            pcwcs = wcs.WCS(pchdr)
            pix = pcwcs.all_world2pix([[pos.ra.deg, pos.dec.deg]],
                1)[0].round().astype(int)[::-1] # For [y,x] indexing!
            pix = pix.clip(1, dims_pcmap) - 1
            pcodefr0 = 100 * pcmap[pix[0], pix[1]]
            str_out = f'Source coding fraction: {pcodefr0:6.2f}%. '
            print(str_out, end='')
            f.write(str_out)
            if pcodefr0 == 0:
                str_out = 'Pointing skipped'
                print(str_out)
                f.write(str_out+'\n')
                if flag_pre:
                    obs0.cat_pre = []
                else:
                    obs0.cat_pos = []
                continue
            print('Downloading pointing data... ', end='')
            t1 = datetime.now()
            obsdir = datadir+prefix+'_'+obs0.type+'_'+obs0.id+'/'
            command = ['wget'   # basic command
                ' -q'           # turn off output
                ' -r -l0'       # recursive retrieval (max depth 0)
                ' -nH'          # no host-prefixed directories
                ' --cut-dirs=7' # also ignore 7 directories
                ' -np'          # do not ascend to parent directory
                f' --directory-prefix={obsdir}' # top directory for output
                ' --no-check-certificate' # don't check server certificate
                ' -c'           # continue partial downloading
                ' -N'           # use same timestamping as remote file
                " -R'index*'"   # reject all 'index*' files
                ' -erobots=off' # turn off Robots Exclusion Standard
                ' --retr-symlinks' # download symbolic links
                ' http://heasarc.gsfc.nasa.gov/FTP/swift/data/obs/'
                f'{yyyy_mm_point}//{obs_id}/'+s for s in ['bat/','auxil/']]
            for command0 in command:
                subp.run(command0.split(' '))
            str_out = f'({(datetime.now()-t1).seconds}s)'
            print('done '+str_out)
            f.write(f'Pointing data downloaded {str_out}\n')
            f.close()

            # Loop over DPH and SNAPSHOT imaging
            datadir_in = obsdir
            cat_tex = []
            for flag_dph in [False, True]:
                gti_ntries = 0
                while gti_ntries < 2:
                    gti_ntries += 1
                    print(f'{70*"-"} {datetime.now():%c}')
                    print(('DPH' if flag_dph else 'SNAPSHOT')+' loop:')
                    print(f'  GTI loop {gti_ntries}: '+
                        ('Standard filtering' if gti_ntries == 1
                            else 'USERGTI filtering only'))
                    datadir_out = (obsdir+'results_'
                        +eband.name+('_dph' if flag_dph else '')+'/')
                    # BATSURVEY command
                    command = ['batsurvey',
                        datadir_in, datadir_out,
                        'energybins='+eband.str,
                        'elimits='+eband.str,
                        'incatalog='+catfile_in,
                        'ncleaniter=2', #Always clean DPH
                        # Apply DPH keyword
                        'timesep='+('DPH' if flag_dph else 'SNAPSHOT'),
                        'filtnames='+('all' if gti_ntries == 1
                            else ('global,pointing,filter_file,startracker,'
                                'st_lossfcn,data_flags,earthconstraints,'
                                'remove_midnight,occultation,usergti')),
                        'gtifile='+gtifile,
                        # Minimum exposure threshold
                        'expothresh=150.0']
                    print(' '.join(command))
                    subp.run(command)
                    # Find if master GTI file was created
                    gtifile_out = glob.glob(datadir_out+'gti/master.gti')
                    if len(gtifile_out) > 0:
                        if gti_ntries == 1:
                            gti_text = 'Standard'
                        elif gti_ntries == 2:
                            gti_text = 'Standard failed. USERGTI only'
                        break
                    else:
                        if gti_ntries == 1:
                            print('Standard GTI filtering failed. ', end='')
                            if flag_dph:
                                print('DPH binning does not work with '
                                    'USERGTI. Aborting')
                                gti_text = ('Standard failed. DPH binning '
                                    'does not work with USERGTI filtering')
                                break
                            else:
                                print('Standard GTI filtering failed.'
                                    ' Trying USERGTI only')
                        elif gti_ntries == 2:
                            print('Standard GTI and USERGTI filtering failed.'
                                ' Aborting')
                            gti_text = 'Standard and USERGTI failed'
                # Get output catalogs
                cat_out = []
                catfile_out = glob.glob(datadir_out+'point_*/point_*_2.cat')
                catfile = (datadir+prefix+'_'+obs0.type+'_'+obs0.id
                    +'_'+coord_str+'_'+eband.name
                    +('_dph' if flag_dph else '')+'.cat')
                if len(catfile_out) > 0:
                    print(('DPH' if flag_dph else 'SNAPSHOT')
                        +' catalogs found:', len(catfile_out))
                else:
                    print('Warning: No '+('DPH' if flag_dph else 'SNAPSHOT')
                        +' catalogs found. Skipping')
                for catfile_out0 in catfile_out:
                    print('Catalog file: '+catfile_out0)
                    t_ss = os.path.basename(catfile_out0).split('_')[1]
                    print(f' {t_ss[:4]}-{t_ss[4:7]}-{t_ss[7:9]}'
                        f':{t_ss[9:11]}...', end='')
                    cat0, hdr0 = fits.getdata(catfile_out0, 1, header=True)
                    cat0_name = cat0['name'].strip()
                    #cat0['name'] = cat0['name'].strip()
                    #cat0['rate'] /= 0.16 #[cts/cm2/sec]
                    #cat0['cent_rate'] /= 0.16
                    #cat0['rate_err'] /= 0.16
                    #cat0['bkg_var'] /= 0.16
                    w = (cat0_name == 'BATSS_'+coord_str).nonzero()[0]
                    if len(w) > 0:
                        cat0 = Table(cat0)
                        for w0 in w:
                            if len(cat_out) == 0:
                                cat0[w0]['CATNUM'] = 1
                                cat_out = Table(cat0[w0])
                                hdr_out = hdr0
                                hdr_out.remove('HISTORY', ignore_missing=True,
                                    remove_all=True)
                                hdr_out['EXTNAME'] = 'BATSURVEY_CATALOG'
                                hdr_out['HDUNAME'] = 'BATSURVEY_CATALOG'
                                # Index for new sources in catalog
                                hdr_out['NEWSRCIN'] = 2
                            else:
                                cat0[w0]['CATNUM'] = hdr_out['NEWSRCIN']
                                hdr_out['NEWSRCIN'] += 1
                                cat_out.add_row(cat0[w0])
                # Save catalog file
                n_det = len(cat_out)
                with open(txtfile,'a') as f:
                    f.write(f'\n{"DPH" if flag_dph else "SNAPSHOT"}'
                        ' processing:\n')
                    f.write(f'GTI filtering: {gti_text}\n')
                    f.write(f'Detections: {n_det if n_det > 0 else "NONE"}\n')
                    if n_det > 0:
                        fits.BinTableHDU(cat_out, hdr_out).writeto(catfile,
                            overwrite=True)
                        print(f'Saved {n_det} detection(s) of'
                            f' BATSS_{coord_str} to file {catfile}')
                        f.write('   '.join([' #',
                            f'{"Time_start":23s}', f'{"Time_stop":23s}',
                            f'{"Exp[s]":7s}', f'{"CF[%]":6s}',
                            'S/N(pix)','S/N(fit)'])+'\n')
                        for cat0 in cat_out:
                            f.write('   '.join([f'{cat0["CATNUM"]:2}',
                                met2Time(cat0['TIME']).iso,
                                met2Time(cat0['TIME_STOP']).iso,
                                f'{cat0["EXPOSURE"]:7.1f}',
                                f'{100*cat0["PCODEFR"]:6.2f}',
                                f'{cat0["CENT_SNR"]:8.2f}',
                                f'{cat0["SNR"]:8.2f}'])
                                +'\n')
                            cat_tex.append({
                                'dt':cat0['TIME']-obs_t0,
                                'exp':cat0['EXPOSURE'],
                                'cf':100*cat0['PCODEFR'],
                                'cent_snr':cat0['CENT_SNR'],
                                'snr':cat0['SNR']
                                })
            if flag_pre:
                obs0.cat_pre = cat_tex
            else:
                obs0.cat_pos = cat_tex
        str_out = ('\nDONE. Processing time: '
            +str(datetime.now()-t0).split('.')[0])
        print(str_out)
        with open(txtfile, 'a') as f:
            f.write(str_out+'\n')
        print('Closed output text file: ', f.name)
    return obs
