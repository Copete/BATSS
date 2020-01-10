from ../../BATSS_reprocess import BATSS_reprocess
from batss_pointing_detect import batss_pointing_detect

det = [
    {'obs_id':'120524_02h21m54s+154s', 'ra':114.798, 'dec':-14.110,
    'eband':'soft', 'err_rad':3.5}, #S/N=9.08, luna1
    {'obs_id':'120524_02h21m54s+154s', 'ra':114.783, 'dec':-14.138,
    'eband':'broad', 'err_rad':3.5}, # S/N=8.92, dahl1
    {'obs_id':'101103_03h03m56s+155s', 'ra': 61.946, 'dec':+15.017,
    'eband':'broad', 'err_rad':3.8}, # S/N=7.88, mond1
    {'obs_id':'100805_06h04m23s+174s', 'ra': 53.633, 'dec':-12.524,
    'eband':'hard' , 'err_rad':4.2}, # S/N=7.10, dahl1
    {'obs_id':'110223_07h27m55s+077s', 'ra':214.623, 'dec':-81.443,
    'eband':'broad', 'err_rad':4.3}, # S/N=6.97, dahl1
    {'obs_id':'090304_22h35m22s+181s', 'ra':211.636, 'dec':+28.826,
    'eband':'soft' , 'err_rad':4.3}, # S/N=6.97, dahl1
    {'obs_id':'110128_06h38m55s+141s', 'ra':179.181, 'dec':-15.160,
    'eband':'broad', 'err_rad':4.5}, # S/N=6.77, dahl1
    {'obs_id':'090407_17h49m59s+173s', 'ra':197.828, 'dec':-66.128,
    'eband':'broad', 'err_rad':4.5}, # S/N=6.76, mond1
    {'obs_id':'070315_03h48m00s+224s', 'ra': 52.230, 'dec':+26.918,
    'eband':'soft' , 'err_rad':4.5}, # S/N=6.75, dahl1
    {'obs_id':'090505_00h49m57s+098s', 'ra':226.423, 'dec':-73.778,
    'eband':'soft' , 'err_rad':4.5}, # S/N=6.71, mond1
    {'obs_id':'120325_11h41m54s+153s', 'ra':178.847, 'dec':+73.202,
    'eband':'soft' , 'err_rad':4.5}, # S/N=6.70, mond1
    {'obs_id':'090106_16h19m58s+084s', 'ra':110.365, 'dec':+27.318,
    'eband':'hard' , 'err_rad':4.6}, # S/N=6.59, mond1
    {'obs_id':'110607_11h06m55s+069s', 'ra':336.615, 'dec':-76.609,
    'eband':'broad', 'err_rad':4.6}, # S/N=6.58, luna1
    {'obs_id':'101018_23h26m56s+165s', 'ra':246.779, 'dec':+31.711,
    'eband':'broad', 'err_rad':4.7}, # S/N=6.52, mond1
    {'obs_id':'100905_03h06m56s+184s', 'ra':181.747, 'dec':-13.118,
    'eband':'broad', 'err_rad':4.7} # S/N=6.51, mond1
    ]

# LaTeX table header
amp=' & '
tab = '\t'
add_tab = lambda str_list, n_tabs=1: [n_tabs*'\t'+str for str in str_list]
table = [
    r'%LaTeX table with BATSS catalog of single unidentified detections'
        ' (pointing data)','',
    r'\begin{longrotatetable}',
    r'\renewcommand{\tabcolsep}{0.4em}',
    r'\tabletypesize{\scriptsize}',
    r'\tablecolumns{12}', '',
    #r'\begin{deluxetable*}{r l r r r r c c r r r r r c r @{$\pm$} l r @{$\pm$} l r @{$\pm$} l}',
    r'\begin{deluxetable*}{r l c r r r r c r r r r}',
    tab+r'%Preamble',
    tab+r'\tablecaption{BATSS catalog of single unidentified detections'
        ' --- pointing data',
    2*tab+r'\label{tab:cat_Neq1_point}}']
table_txt = ['BATSS catalog of single unidentified detections'
    ' --- pointing data','']

#TABLE HEADER
#Header for all pages
table_header_batss = [
    r'\colhead{\multirow{2}{*}{\#}}'+amp,
    r'\colhead{\multirow{2}{*}{Name}}'+amp,
    #r'\colhead{RA}'+amp,
    #r'\colhead{Dec}'+amp,
    #r'\colhead{Gal.lon.}'+amp,
    #r'\colhead{Gal.lat.}'+amp,
    #r'\colhead{$r_{90}$}'+amp,
    r'\colhead{\multirow{2}{*}{Observation}}'+amp,
    #r'\colhead{Exp}'+amp,
    #r'\colhead{CF}'+amp,
    r'\multicolumn{4}{c}{Preceding}'+amp+amp,
    r'\multicolumn{4}{c}{Following} \\',
    r'\cline{4-7} \cline{9-12}',
    amp+amp+amp, #'\colhead{[$^\circ$]}'+amp,
    #r'\colhead{[$^\circ$]}'+amp,
    #r'\colhead{[$^\circ$]}'+amp,
    #r'\colhead{[$^\circ$]}'+amp,
    #r"\colhead{[$'$]}"+amp+amp,
    #r'\colhead{[ks]}'+amp,
    #r'\colhead{[\%]}'+amp,
    r'\colhead{$\Delta T_0$[s]}'+amp,
    r'\colhead{Exp[s]}'+amp,
    r'\colhead{CF[\%]}'+amp,
    r'\colhead{$S/N$}'+amp+amp,
    r'\colhead{$\Delta T_0$[s]}'+amp,
    r'\colhead{Exp[s]}'+amp,
    r'\colhead{CF[\%]}'+amp,
    r'\colhead{$S/N$}'
    #r'\colhead{Soft}'+amp,
    #r'\colhead{Hard}'+amp,
    #r'\colhead{Broad}'+amp+amp,
    #r'\multicolumn{2}{c}{Soft}'+amp,
    #r'\multicolumn{2}{c}{Hard}'+amp,
    #r'\multicolumn{2}{c}{Broad}']
    ]
table_header = table_header_batss
subtable_header = table_header + ['\\ \hline']
#Include table header
table += (
    [tab+r'\tablehead{']
    + add_tab(table_header,2)
    + add_tab([
        r'}',
        r'%Table data',
        r'\startdata'])
    )

# Call batss_pointing_detect and get table entries
for i, det0 in enumerate(det):
#for i, det0 in enumerate([det[5]]):
    # status = BATSS_reprocess(det0['obs_id'])
    obs0 = batss_pointing_detect(det0['obs_id'], det0['ra'], det0['dec'],
        det0['eband'], det0['err_rad'])[0]
    for j in range(max(1,len(obs0.cat_pre),len(obs0.cat_pos))):
        if j == 0:
            table += [tab+f"{1+i}{amp}{obs0.src_name}{amp}"
                f"\\nolinkurl{{{obs0.id}}}"]
            line0 = tab+amp
        else:
            line0 = tab+3*amp
        if j < len(obs0.cat_pre):
            det1 = obs0.cat_pre[j]
            line0 += (f"${det1['dt']:+.1f}${amp}{det1['exp']:.1f}{amp}"
                f"{det1['cf']:.1f}{amp}${det1['cent_snr']:.2f}${2*amp}")
        else:
            line0 += 5*amp
        if j < len(obs0.cat_pos):
            det1 = obs0.cat_pos[j]
            line0 += (f"${det1['dt']:+.1f}${amp}{det1['exp']:.1f}{amp}"
                f"{det1['cf']:.1f}{amp}${det1['cent_snr']:.2f}$")
        else:
            line0 += 3*amp
        table += [line0 + r' \\']
    if i < len(det)-1:
        table += [tab + r'\hline']

#End of table
table += ([
	tab+r'\enddata',
    r'\end{deluxetable*}',
    r'\end{longrotatetable}'
    ])

#Write output file
texfile = 'tab_cat_Neq1_pointing.tex'
with open(texfile,'w') as f:
    f.write('\n'.join(table))
print('Closed output text file: ', f.name)
