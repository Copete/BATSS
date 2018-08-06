import astropy.units as u

class BATSS_eband:
    #
    def __init__(self, name):
        self.name = name
        if self.name == 'soft':
            self.emin = 15 * u.keV
            self.emax = 50 * u.keV
            self.str = '15-50 keV'
        elif self.name == 'hard':
            self.emin = 50 * u.keV
            self.emax = 150 * u.keV
            self.str = '50-150 keV'
        elif self.name == 'broad':
            self.emin = 15 * u.keV
            self.emax = 150 * u.keV
            self.str = '15-150 keV'
        else:
            raise #Exception!
