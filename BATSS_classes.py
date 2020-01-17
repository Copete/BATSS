import os, glob
import numpy as np
import astropy.units as u

class BATSS_eband:
    #
    def __init__(self, name):
        self.name = name
        if self.name == 'soft':
            self.emin = 15 * u.keV
            self.emax = 50 * u.keV
            self.str = '15-50'
            self.str_keV = self.str+' keV'
        elif self.name == 'hard':
            self.emin = 50 * u.keV
            self.emax = 150 * u.keV
            self.str = '50-150'
            self.str_keV = self.str+' keV'
        elif self.name == 'broad':
            self.emin = 15 * u.keV
            self.emax = 150 * u.keV
            self.str = '15-150'
        else:
            raise ValueError("eband name must be 'soft', 'hard' or 'broad'")
        self.str_keV = self.str+' keV'


class BATSS_dir:
    '''
    BATSS directory structure
    '''
    root = '/data/luna0/acopete/BATSS/' #Root directory for all BATSS data

# define root directory!

class BATSS_observation:
    '''
    BATSS generic observation class
    '''
    root = ''
    def __init__():
        '''
        Instantiate generic BATSS observation
        '''
        self.type = ''
        self.id = ''
        self.fitsfile = ''  # FITS file (archival)
        self.fitsfile_realtime = '' # FITS file (realtime)
        self.queuefile = '' # Queue file (archival)
        self.queuefile_realtime = '' # Queue file (realtime)
        self.pcfile = '' # Partial coding map file
        self.pcfile_realtime = '' # Partial coding map file
        self.attfile = '' # Attitude file
        self.attfile_realtime = '' # Attitude file

class BATSS_slew(BATSS_observation):
    '''
    BATSS single-slew class
    '''
    type = 'slew'
    def __init__(self, id):
        '''
        Instatiate BATSS single-slew class object
        '''
        # Parse slew ID
        self.id = id
        assert isinstance(self.id, str)
        assert len(self.id) is 21
        # Get observation directory
        root = BATSS_dir.root
        yymmdd = self.id[:6]
        yyyy_mm = '20'+yymmdd[:2]+'_'+yymmdd[2:4]
        obs_dir = [root+'products/'+yyyy_mm+'/'+self.type+suffix+'/'
            +yymmdd+'/'+self.id+'/'
            for suffix in ['','_realtime']]
#        obs_fitsfile = [root+'products/'+yyyy_mm+'/'+self.type+suffix+'/'
#            +yymmdd+'/'+self.id+'/'+self.type+'_'+self.id+'.fits'
#            for suffix in ['','_realtime']]
        obs_queuefile = [root+'products/'+yyyy_mm+'/queue'+suffix+'/'
            +'queue_'+yymmdd+'_'+self.type+'.fits'
            for suffix in ['','_realtime']]
        # Archival files
        #if os.path.exists(obs_fitsfile[0]):
        if os.path.exists(obs_dir[0]):
            fitsfile = obs_dir[0]+self.type+'_'+self.id+'.fits'
            if os.path.exists(fitsfile):
                self.fitsfile = os.path.realpath(fitsfile)
                self.dir = os.path.dirname(self.fitsfile)+'/'
                pcfile = glob.glob(self.dir+self.type+'_'+self.id+'.img.pc*')
                self.pcfile = pcfile[0] if len(pcfile)==1 else ''
            else:
                # For broken link, set directory to root disk directory
                self.dir = obs_dir[0]
                self.fitsfile = ''
                self.pcfile = ''
            attfile = glob.glob(self.dir+self.type+'_'+self.id+'.att*')
            self.attfile = attfile[0] if len(attfile)==1 else ''
        else:
            self.dir = ''
            self.fitsfile = ''
            self.pcfile = ''
            self.attfile = ''
        if os.path.exists(obs_queuefile[0]):
            self.queuefile = os.path.realpath(obs_queuefile[0])
        else:
            self.queuefile = ''
        # Real-time files
        if os.path.exists(obs_fitsfile[1]):
            self.fitsfile_realtime = os.path.realpath(obs_fitsfile[1])
            self.dir_realtime = os.path.dirname(self.fitsfile_realtime)+'/'
            pcfile = glob.glob(self.dir_realtime+self.type+'_'+ self.id+'.img.pc*')
            self.pcfile_realtime = pcfile[0] if len(pcfile)==1 else ''
            attfile = glob.glob(self.dir_realtime+self.type+'_'+ self.id+'.att*')
            self.attfile_realtime = attfile[0] if len(attfile)==1 else ''
        else:
            self.fitsfile_realtime = ''
            self.dir_realtime = ''
            self.pcfile_realtime = ''
            self.attfile_realtime = ''
        if os.path.exists(obs_queuefile[1]):
            self.queuefile_realtime = os.path.realpath(obs_queuefile[1])
        else:
            self.queuefile_realtime = ''
