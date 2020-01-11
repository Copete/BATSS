;Produce output tables of all BATSS single-observation (N=1) candidates
@/data/luna0/acopete/BATSS/pipeline/BATSS_general.pro
@/data/luna0/acopete/BATSS/tests/HEASARC/HEASARC_tables.pro ;Load HEASARC tables script
; 01/10/20 Update to produce new table for BATSS paper 4

;Inverse error function
FUNCTION INVERF, erfx
on_error, 2
; ERROR FUNCTION CAN ONLY RETURN 0 <= ERRORF(X) <= 1, SO
; THE INVERSE ERROR FUNCTION OF ANYTHING GREATER THAN ONE IS
; MEANINGLESS...
if (total((erfx le 1d0) AND (erfx ge 0)) ne N_elements(erfx)) then $
    message, 'The range of the error function is 0 < erf(x) <= 1!'
; IS ERFX WITHIN MACHINE PRECISION OF UNITY...
type = size(erfx,/TYPE)
epsn = (machar(DOUBLE=(type eq 5L))).epsneg
; CHECK THE MACHINE PRECISION HERE...
p = 1d0 - (erfx - epsn*( (erfx - 0.5*epsn) eq fix(1.,TYPE=type) ))
p = 0.5d0*p
t = sqrt(-2d0*alog(p))
num =  (0.010328d0*t + 0.802853d0)*t + 2.515517d0
den = ((0.001308d0*t + 0.189269d0)*t + 1.432788d0)*t + 1d0
return, 0.70710678118654752440d0 * ((t - num/den) > 0)
END

root = '/data/luna0/acopete/BATSS/'
;testroot = root+'Papers/Paper4_BATSS_survey/cat_Neq1/' ;Old location
testroot = root+'GitHub/BATSS/Paper4_BATSS_survey/cat_Neq1/'  ;New location in Git repository

results_only = 0B               ;Set to display results only

snr_thresh = 6.5
flag_r99 = 0B ;Use 99% radii (rather than 90% radii) for matching

;heasarc_table = 'bzcat' ;ASDC BZCAT (blazar catalog)
;heasarc_table = 'rassbsc' ;ROSAT All-Sky Survey: Bright Sources
;heasarc_table = 'rassvars' ;RASS X-Ray Variable Sources Catalog
;heasarc_table = 'aavsovsx' ;AAVSO International Variable Star Index
;heasarc_table = 'veroncat' ;Veron Catalog of Quasars & AGN, 13th Edition
;heasarc_table = 'crates' ;CRATES Flat-Spectrum Radio Source Catalog
;heasarc_table = 'qorgcat' ;All-Sky Optical Catalog of Radio/X-Ray Sources
;heasarc_table = 'xmmslewcln' ;XMM-Newton Slew Survey Clean Source Catalog, v1.5
;heasarc_table = 'xmmslewful' ;XMM-Newton Slew Survey Full Source Catalog, v1.5

;Special characters
amp=' & '
tab=string(9B)

;Output files
texfile = testroot+'tab_cat_Neq1_HEASARC_all.tex'
txtfile = testroot+'tab_cat_Neq1_HEASARC_all.txt'
psfile  = testroot+'tab_cat_Neq1_HEASARC_all.ps'

;Initialize table
n_col = 20 ;Number of table columns
table = $
   ['%LaTeX table with BATSS catalog of single unidentified detections','', $
    '\clearpage', $
    '\LongTables', $
    '\begin{landscape}', $
    '\renewcommand{\arraystretch}{1.10}', $
    '\renewcommand{\tabcolsep}{0.4em}', $
    '\tabletypesize{\scriptsize}', $
    '\tablecolumns{20}', $
    '\begin{deluxetable}{r l r r r r c c r r r r r c r @{$\pm$} l r @{$\pm$} l r @{$\pm$} l}', $
    tab+['%Preamble', $
         '\tablecaption{BATSS catalog of single unidentified detections', $
         tab+'\label{tab:cat_Neq1}}']]
table_txt = ['BATSS catalog of single unidentified detections','']

;TABLE HEADER
;Header for all pages
table_header_batss = $
   ['\colhead{\multirow{2}{*}{\#}}'+amp, $
    '\colhead{\multirow{2}{*}{Name}}'+amp, $
    '\colhead{RA}'+amp, $
    '\colhead{Dec}'+amp, $
    '\colhead{Gal.lon.}'+amp, $
    '\colhead{Gal.lat.}'+amp, $
    '\colhead{$r_{90}$}'+amp, $
    '\colhead{\multirow{2}{*}{Observation}}'+amp, $
    '\colhead{Exp}'+amp, $
    '\colhead{CF}'+amp, $
    '\multicolumn{3}{c}{$S/N$}'+amp+amp, $
    '\multicolumn{6}{c}{Est. Flux [mCrab]} \\', $
    '\cline{11-13} \cline{15-20}', $
    amp+amp+'\colhead{[$^\circ$]}'+amp, $
    '\colhead{[$^\circ$]}'+amp, $
    '\colhead{[$^\circ$]}'+amp, $
    '\colhead{[$^\circ$]}'+amp, $
    "\colhead{[$'$]}"+amp+amp, $
    '\colhead{[ks]}'+amp, $
    '\colhead{[\%]}'+amp, $
    '\colhead{Soft}'+amp, $
    '\colhead{Hard}'+amp, $
    '\colhead{Broad}'+amp+amp, $
    '\multicolumn{2}{c}{Soft}'+amp, $
    '\multicolumn{2}{c}{Hard}'+amp, $
    '\multicolumn{2}{c}{Broad}']
table_header = table_header_batss
subtable_header = $
   [table_header, $
    '\\ \hline']
;Include table header
table = $
   [table, $
    tab+[$
   '\tablehead{', $
   tab+table_header, $
   '}', $
   '%Table data', $
   '\startdata']]

;TABLE BODY
;Define energy bins, Crab fluxes
ebins = [{str:'15-50keV' ,e_min:15,e_max:50}, $
         {str:'50-150keV',e_min:50,e_max:150}, $
         {str:'15-150keV',e_min:15,e_max:150}]
Crabflux = (10D/1.05)*(ebins.e_min^(-1.05)-ebins.e_max^(-1.05))/2

;Get Swift GRB catalog
digit = strtrim(indgen(10),2)
catfile      = testroot+'grb_table.txt'
catfile_html = testroot+'grb_table.html'
catfile_new  = testroot+'grb_table_new.txt'
spawn, 'wget -q -O '+catfile_html+$
       ' "https://swift.gsfc.nasa.gov/archive/grb_table/'+$
       'table.php?obs=All+Observatories&year=All+Years&restrict=none'+$
       '&grb_time=1&grb_trigger=1&bat_ra=1&bat_dec=1&bat_err_radius=1'+$
       '&bat_t90=1&bat_fluence=1&bat_err_fluence=1&bat_1s_peak_flux=1'+$
       '&bat_err_1s_peak_flux=1&bat_photon_index=1&bat_err_photon_index=1'+$
       '&xrt_ra=1&xrt_dec=1&xrt_err_radius=1"'

lunr=0 & lunw=0 & liner=''
openr, lunr, catfile_html, /get_lun
openw, lunw, catfile_new, /get_lun
repeat begin
   repeat readf, lunr, liner until (strmid(liner,0,3) eq '<tr') or eof(lunr)
   if eof(lunr) then break
   linew = ''
   repeat begin
      readf, lunr, liner
      if strmid(liner,0,3) eq '<td' then begin
         p1 = 0
         repeat begin
            p0 = strpos(liner,'>',p1)
            p1 = strpos(liner,'<',p0)
         endrep until p1-p0 gt 1
         linew = linew + (linew eq '' ? '':tab) + strmid(liner,p0+1,p1-p0-1)
      endif
   endrep until strmid(liner,0,5) eq '</tr>'
   if linew ne '' then printf, lunw, linew
endrep until eof(lunr)
free_lun, lunr, lunw
if file_test(catfile) then begin
   lun0=0 & lun1=0 & line0='' & line1=''
   openr, lun0, catfile, /get_lun
   openr, lun1, catfile_new, /get_lun
   flag_diff = 0B
   while not eof(lun1) do begin
      if eof(lun0) then begin
         flag_diff = 1B
         break
      endif
      readf, lun1, line1
      readf, lun0, line0
      if line0 ne line1 then begin
         flag_diff = 1B
         break
      endif
   endwhile
   free_lun, lun0, lun1
endif else flag_diff = 1B
if flag_diff then file_copy, catfile_new, catfile, /overwrite
;-Read current GRB catalog file
lun=0 & line=''
openr, lun, catfile, /get_lun
cat1 = 0
;For GRB catalog from Swift website
href0='http://heasarc.gsfc.nasa.gov/docs/swift/archive/grb_table/'+$
      'grb_lookup.php?grb_name='
grb=0
while not eof(lun) do begin
   readf, lun, line
   if strmid(line,0,1) eq '!' then continue
   column = str_sep(line,string(9B))
   ;Get XRT position if possible; if not, use BAT position
   RA  = strtrim(column[13],2)
   Dec = strtrim(column[14],2)
   if (strmid(RA, 0,3) eq 'n/a') or (strmid(RA, 0,3) eq 'TBD') or $
      (strmid(Dec,0,3) eq 'n/a') or (strmid(Dec,0,3) eq 'TBD') then begin
      RA  = double(column[3])      ;[deg]
      Dec = double(column[4])      ;[deg]
   endif else begin
      if RA eq '19:2532.61' then RA='19:25:32.61' ;(TEMP??? FOR GRB 101017A)
      RA0 = str_sep(RA,':')
      if n_elements(RA0) ne 3 then begin
         RA0 = str_sep(strcompress(RA),' ')
         if n_elements(RA0) ne 3 then begin
;            message, 'Invalid RA format: "'+RA+'" Revise'
            print, 'Warning: Invalid RA format "'+RA+'"'
            RA  = double(column[3])      ;[deg]
            Dec = double(column[4])      ;[deg]
            goto, grb_entry
         endif
      endif
      RA = double(RA0)
      RA = 15D*(RA[0]+(RA[1]/60D)+(RA[2]/3600D)) ;[deg]
      Dec_sign = (strmid(Dec,0,1) eq '-' ? -1 : 1)
      Dec0 = str_sep(Dec,':')
      if n_elements(Dec0) ne 3 then begin
         Dec0 = str_sep(strcompress(Dec),' ')
         if n_elements(Dec0) ne 3 then begin
;           message, 'Invalid Dec format: "'+Dec+'" Revise'
            print, 'Warning: Invalid Dec format "'+Dec+'"'
            RA  = double(column[3])      ;[deg]
            Dec = double(column[4])      ;[deg]
            goto, grb_entry
         endif
      endif
      Dec = abs(double(Dec0))
      Dec = Dec_sign*(Dec[0]+(Dec[1]/60D)+(Dec[2]/3600D)) ;[deg]
   endelse
   t90 = strtrim(column[6],2)
   t90 = (total(strmid(t90,0,1) eq digit) eq 0 ? 0. : float(t90))
   fl = strtrim(column[7],2)
   fl = (total(strmid(fl,0,1) eq digit) eq 0 ? 0. : float(fl))
   d_fl = strtrim(column[8],2)
   d_fl = (total(strmid(d_fl,0,1) eq digit) eq 0 ? 0. : float(d_fl))
   grb_entry:
   grb0 = {name:'GRB '+column[0], $
           RA:RA, $
           Dec:Dec, $
           t90:t90, $
           fl:fl, $
           d_fl:d_fl, $
           href:href0+column[0]}
   grb = (size(grb,/tname) eq 'STRUCT' ? [grb,grb0] : [grb0])
endwhile
free_lun, lun
;grb_all = grb[where((grb.t90 gt 0) and (grb.fl gt 0),n_grb_all)]
grb_all = grb  &  n_grb_all = n_elements(grb)
help, n_grb_all

;Get BATSS-only GRBs
print, 'Reading BATSS-only GRBs... ', f='(a,$)'
grb = [{name:'GRB 070326' , trigger:100042L, archival:0B, met:196619290.5D, align:1}, $
       {name:'GRB 071212' , trigger:100112L, archival:1B, met:219122559.0D, align:1}, $
       {name:'GRB 080130' , trigger:100177L, archival:0B, met:223344002.0D, align:1}, $
       {name:'GRB 080702B', trigger:100478L, archival:0B, met:236653844.0D, align:0}, $
       {name:'GRB 080806',  trigger:100583L, archival:1B, met:239709597.0D, align:0}, $
       {name:'GRB 081025',  trigger:100762L, archival:0B, met:246615786.6D, align:-1}, $
       {name:'GRB 081203B', trigger:100828L, archival:0B, met:250005139.2D, align:1}, $
       {name:'GRB 081211B', trigger:100851L, archival:0B, met:250668919.2D, align:0}, $
       {name:'GRB 090118',  trigger:000024L, archival:0B, met:jd2met(julday(01,18,2009)), align:0}, $
       {name:'GRB 090306B', trigger:101004L, archival:0B, met:258073644.0D, align:0}, $
       {name:'GRB 090418B', trigger:101098L, archival:0B, met:261737965.0D, align:0}, $
       {name:'GRB 090823',  trigger:101320L, archival:2B, met:272736691.0D, align:0}, $ ;NOT reported by BATSS first
       {name:'GRB 090929A', trigger:101376L, archival:2B, met:275891588.8D, align:0}, $ ;NOT reported by BATSS first
       {name:'GRB 100120A', trigger:101559L, archival:1B, met:285684740.4D, align:-1}, $
       {name:'GRB 101004A', trigger:101962L, archival:1B, met:307921980.6D, align:0}, $
       {name:'GRB 110107A', trigger:102225L, archival:2B, met:316127687.8D, align:0}, $ ;NOT reported by BATSS first
       {name:'GRB 110319B', trigger:102413L, archival:2B, met:322256047.0D, align:0}, $ ;NOT reported by BATSS first
       {name:'GRB 110906A', trigger:102619L, archival:0B, met:jd2met(julday(09,06,2011)), align:-1}, $
       {name:'GRB 111011A', trigger:102678L, archival:1B, met:jd2met(julday(10,11,2011)), align:0}, $
       {name:'GRB 120524A', trigger:102967L, archival:1B, met:jd2met(julday(05,24,2012)), align:0}$ ;Unreported BATSS GRB
       ]
;-Get all BATSS candidates
restore, root+'products/triggers/hk/BATSS_matched.idl'
cand_matched[where(cand_matched.trigger eq 101774L)].name_cat = 'GRB 100728A' ;TEMP???
;-GRB_BATSS is CAND structure for all single-observation BATSS-only GRBs
n_grb_batss = n_elements(grb)
for i=0,n_grb_batss-1 do begin
   grb0 = grb[i]
   case grb0.trigger of
      000024L:begin             ;GRB 090118
         ra0  = 49.865
         dec0 = +18.478
         euler, ra0, dec0, glon0, glat0, /select
         cand0 = {batss_candidate, trigger:grb0.trigger, name:'BATSS_'+string(grb0.trigger,f='(i06)'), $
                  name_cat:grb0.name, datatype:'archival', $ ;but it's actually 'realtime'
                  time:grb0.met, snr:8.0D, cent_snr:8.0D, ra:ra0, dec:dec0, glon:glon0, glat:glat0, err_rad:3.69, $
                  n_obs:1, first:-1L, last:-1L, crit:byte([0,1,0,0,0,1]), index:9, href:'', html:'', ascii:'', $
                  trig_ver:1, trig_statcode:1, trig_statcmt:'', trig_id_link:'', gcn_flag:1B, action:0B}
      end
      else: begin
         w0 = where((cand_matched.trigger eq grb0.trigger) and $
                    (cand_matched.n_obs eq 1), $ ;Single-observation candidates only
                    n0)
         cand0 = cand_matched[w0]
         cand0.name_cat = grb0.name
      endelse
   endcase
   grb_batss = (i eq 0 ? [cand0] : [grb_batss, cand0])
endfor
print, 'done'

;Known source catalogs:
;I)Hard X-ray Transient Catalog (HTML version)
print, 'Reading BAT Transient Catalog... ', f='(a,$)'
catfile_remote = $
   'http://heasarc.gsfc.nasa.gov/docs/swift/results/transients/index.html'
htmlfile = testroot+'BAT_transients.html'
spawn, 'wget -q -N '+catfile_remote+' --output-document='+htmlfile
lun=0 & line=''
openr, lun, htmlfile, /get_lun
trcat = 0
while not eof(lun) do begin
   repeat begin
      readf, lun, line
   endrep until (strmid(line,0,15) eq '<tr align=left>') or eof(lun)
   if eof(lun) then break
   readf, lun, line
   if strmid(line,0,4) ne '<td>' then continue
   href0 = (str_sep(strmid(line,strpos(line,'href="')+6),'"'))[0]
   line0 = str_sep(line,'<td>')
   name0 = str_sep(line0[2],'>')
   w = where(strmid(name0,0,1) ne '<',n)
   name0 = strtrim((str_sep(name0[w[0]],'<'))[0],2)
   ra0 = str_sep(line0[3],'>')
   w = where(strmid(ra0,0,1) ne '<',n)
   ra0  = double((str_sep(ra0[w[0]],'<'))[0])
   dec0 = str_sep(line0[4],'>')
   w = where(strmid(dec0,0,1) ne '<',n)
   dec0 = double((str_sep(dec0[w[0]],'<'))[0])
   cat0 = {name:name0, $
           RA:ra0, $
           Dec:dec0, $
           catalog:'BAT Transients', $
           href:'http://heasarc.nasa.gov/docs/swift/results/transients/'+href0}
   trcat = (size(trcat,/tname) eq 'STRUCT') ? [trcat,cat0] : [cat0]
endwhile
free_lun, lun
print, 'done'

;II)BAT 70-month survey catalog
print, 'Reading BAT 70-month survey catalog... ', f='(a,$)'
catfile = root+'/products/catalogs/transients/BAT_survey_70mo_121120.fits'
trcat0 = mrdfits(catfile,1,trcathdr0,/silent)
for i=0,n_elements(trcat0)-1 do begin
   trcat1 = trcat0[i]
   trcat1.bat_name = strtrim(trcat1.bat_name,2)
   trcat1.counterpart_name = strtrim(trcat1.counterpart_name,2)
   href1 = 'SWIFT_'+strtrim((str_sep(trcat1.bat_name,'SWIFT '))[1],2)
   cat0 = {name:trcat1.bat_name+' ('+trcat1.counterpart_name+')', $
           RA:double(trcat1.ra), $
           Dec:double(trcat1.dec), $
           catalog:'BAT 70-month', $
           href:'http://swift.gsfc.nasa.gov/docs/swift/results/bs70mon/'+href1}
   trcat = (size(trcat,/tname) eq 'STRUCT') ? [trcat,cat0] : [cat0]
endfor
print, 'done'

;-Read names of HEASARC tables to be searched
;heasarc_search_file = 'batss_HEASARC_catalogs.txt'
;file_copy, dataroot+heasarc_search_file, testroot, /allow_same
;lun=0 & line=''
;heasarc_search = 0
;openr, lun, testroot+heasarc_search_file, /get_lun
;while not eof(lun) do begin
;   readf, lun, line
;   line0 = strsplit(strcompress(strtrim(line,2)),' ',/extract)
;   if strmid(line0[0],0,1) eq '*' then begin
;      heasarc_search0 = line0[1]
;      heasarc_search = $
;         (size(heasarc_search,/tname) eq 'STRING' ? $
;          [temporary(heasarc_search),heasarc_search0]:[heasarc_search0])
;   endif
;endwhile
;TEMP
;heasarc_search = ['nvss',$ ;TEMP???
;                  'milliquas','rc3','veroncat','crates','qorgcat','rass2mass',$
;                  'rassusnoid','rospspctotal','wgacat','aavsovsx','gcvs',$
;                  'gcvsnsvars','rassdsstar','xmmslewcln','xmmslewful']
;heasarc_search = ['rassmaster','rosmaster',$ ;'rass2mass','rassdssagn','rassdsstar',$ ;ROSAT
;                  'xmmmaster',$ ;'xmmslewcln','xmmslewful',$ ;XMM
;                  'aavsovsx',$ ;VSX
;                  'veroncat']  ;Veron QSOs
;heasarc_search = [heasarc_table] ;Match to only 1 table at a time
;heasarc_search = [''] ;Do not search HEASARC catalogs
;heasarc_search = ['bzcat',HEASARC_tables()] ;Search ALL tables
heasarc_search = ['bzcat'] ;(01/11/20) Search just BZCAT until HEASARC_tables is fixed!
heasarc = 0
n_heasarc = 0
if keyword_set(HEASARC_search) then begin
   for c=0,n_elements(heasarc_search)-1 do begin
      HEASARC_search0 = HEASARC_search[c]
      case HEASARC_search0 of
         'bzcat':begin
            ;-Include 'bzcat' catalog
            bzcat_file = testroot+'120806_asdc_bzcat.txt'
            if file_test(bzcat_file) then begin
               print, "Including catalog 'bzcat'... ", f='(a,$)'
               lun=0 & line=''
               bzcat = 0
               openr, lun, bzcat_file, /get_lun
               readf, lun, line ;Skip first line
               while not eof(lun) do begin
                  readf, lun, line
                  line0 = strtrim(strsplit(line,'|',/extract,count=n),2)
                  RA0 = double(strsplit(line0[2],' ',/extract))
                  RA0 = 15D * (RA0[0]+(RA0[1]/60D)+(RA0[2]/3600D))
                  Dec0 = strsplit(line0[3],' ',/extract)
                  Dec0 = [(strmid(Dec0[0],0,1) eq '-' ? -1:1), double(abs(Dec0))]
                  Dec0 = Dec0[0] * (Dec0[1]+(Dec0[2]/60D)+(Dec0[3]/3600D))
                  bzcat0 = {number:fix(line0[0]), name:line0[1], $
                            RA:double(RA0), Dec:double(Dec0), $
                            z:float(line0[4]), rmag:float(line0[5]), $
                            src_class:line0[6]}
                  bzcat = (size(bzcat,/tname) eq 'STRUCT' ? $
                           [temporary(bzcat),bzcat0]:[bzcat0])
               endwhile
               free_lun, lun
               heasarc0 = {table:'bzcat',mission:'ASDC',$
                           description:'ASDC Multi-frequency Catalogue of Blazars (07/01/11)',$
                           fields:'',sortcol:'',filter:''}
               heasarc = (size(heasarc,/tname) eq 'STRUCT' ? $
                          [heasarc,heasarc0] : [heasarc0])
               n_heasarc = 1 + n_heasarc
               print, 'done'
            endif
         end
         else:begin
            table0 = HEASARC_tables(HEASARC_search0, $
                                    mission=mission0, description=description0)
            if table0 ne '' then begin
               print, "Including catalog '"+table0+"'... ", f='(a,$)'
               heasarc0 = {table:table0, mission:mission0, description:description0, $
                           fields:'', sortcol:'', filter:''}
               heasarc = (size(heasarc,/tname) eq 'STRUCT' ? $
                          [heasarc,heasarc0] : [heasarc0])
               n_heasarc = n_heasarc + 1
               print, 'done'
            endif
         end
      endcase
   endfor
   if n_heasarc gt 0 then begin
      flag = bytarr(n_heasarc)
      flag[uniq(heasarc.table,sort(heasarc.table))] = 1B
      heasarc = heasarc[where(flag,n_heasarc)]
   endif
   print, strtrim(n_heasarc,2)+' unique HEASARC catalogs to be searched'
   heacat_suffix = '_HEASARC'
   ;-Table fields for select catalogs
   for c=0,n_heasarc-1 do begin
;      heacat_suffix = heacat_suffix+$
;                      ((c gt 0) and (boolean eq 'AND') ? '_AND2':'')+$
;                      '_'+heasarc[c].table
      case heasarc[c].table of
         else:begin
            fields0 = ['Name','Offset']
            ;fields0 = ['Name','RA','Dec','Radius','Offset']
            sortcol0 = '_offset'
            filter0 = ''
         end
      endcase
      for f=0,n_elements(fields0)-1 do $
         heasarc[c].fields = heasarc[c].fields + (f eq 0 ? '':string(9B)) + fields0[f]
      heasarc[c].sortcol = sortcol0
      heasarc[c].filter = filter0
   endfor
;   heamatch_notes = $
;      [heamatch_notes, $
;       'HEASARC catalogs searched ('+strtrim(n_heasarc,2)+'):', $
;       spc+'Mission: '+heasarc.mission+', Catalog: '+heasarc.table+$
;       '. '+heasarc.description, $
;       'Number of randomizations of BATSS catalog: '+strtrim(n_rnd,2)]
;   flag_heamatch = 1B
endif else begin
   heacat_suffix = ''
   n_heasarc = 0
;   flag_heamatch = 0B
endelse

;Bad GTI intervals
gti_bad = $
   ;-NOT really bad, GRB just outside error circle
   [{start:jd2met(julday(03,26,2007,16,28,00)), $
     stop: jd2met(julday(03,26,2007,16,28,00+059))},$
    {start:jd2met(julday(07,28,2010,02,14,56)), $
     stop: jd2met(julday(07,28,2010,02,14,56+193))},$
    ;-Bad attitude intervals
    {start:jd2met(julday(02,08,2008,13,24,25)), $
     stop: jd2met(julday(02,08,2008,13,24,25+061))},$
    {start:jd2met(julday(07,27,2008,17,29,19)), $
     stop: jd2met(julday(07,27,2008,17,34,04+076))},$
    {start:jd2met(julday(10,15,2008,09,50,00)), $
     stop: jd2met(julday(10,15,2008,10,28,49+128))},$
    {start:jd2met(julday(02,19,2009,16,48,00)), $
     stop: jd2met(julday(02,19,2009,17,54,30))},$
    {start:jd2met(julday(02,25,2009,18,00,57)), $
     stop: jd2met(julday(02,25,2009,18,00,57+169))},$
    {start:jd2met(julday(07,26,2009,04,58,00)), $
     stop: jd2met(julday(07,26,2009,05,46,32+058))},$
    {start:jd2met(julday(10,24,2009,12,03,57)), $
     stop: jd2met(julday(10,24,2009,12,07,32+047))},$
    {start:jd2met(julday(08,15,2010,21,48,41)), $
     stop: jd2met(julday(08,15,2010,22,41,25+070))}]
n_gti_bad = n_elements(gti_bad)
help, n_gti_bad

;Initialize PostScript file
set_plot, 'PS'
device, /color, bits_per_pixel=8, filename=PSfile, /inches, $
        /portrait, xoffset=1.0, yoffset=6.0, xsize=6.5, ysize=4.0
        ;/landscape, xoffset=0.5, yoffset=10.5, xsize=10, ysize=7.5
normal = [1.0,1.0] ;Size of image in normal coordinates
thick=3 & chthick=3
chsize = 1.5 ;Character size
loadct, 39, /silent
;-Set up Aitoff projection
map_set, 0, 0, 0, $
         position=[0,0,normal[0],normal[1]], $ ;Normal coordinates
         /aitoff, /isotropic, /noborder, /reverse, /grid, /noerase, $
         /horizon, glinethick=thick, $
         title='!5BATSS single unidentified detections, N=1, S/N>=6', $
         charsize=chsize
legend = 0

;Loop over observation types
for type=0,6 do begin
   t1 = systime(1)
   detfile0 = root+'products/detections/BATSS/BATSS_UNKNOWN/'
   case type of
      ;-Survey
      0:begin
         obs_type = 'Survey'
         color0 = 15
         detfile0 = detfile0+'survey/BATSS_survey.det.fits.gz'
      end
      ;-Yearly
      1:begin
         obs_type = 'Yearly'
         color0 = 20
         detfile0 = detfile0+'yearly/year_????.det.fits.gz'
      end
      ;-Monthly
      2:begin
         obs_type = 'Monthly'
         color0 = 25
         detfile0 = detfile0+'????_??/monthly/month_????.det.fits.gz'
      end
      ;-Weekly
      3:begin
         obs_type = 'Weekly'
         color0 = 50
         detfile0 = detfile0+'????_??/weekly/week_??????.det.fits.gz'
      end
      ;-Daily
      4:begin
         obs_type = 'Daily'
         color0 = 150
         detfile0 = detfile0+'????_??/daily/day_??????.det.fits.gz'
      end
      ;-Orbital
      5:begin
         obs_type = 'Orbital'
         color0 = 250
         detfile0 = detfile0+'????_??/orbital/??????/orbit_??????_??h??m??s.det.fits.gz'
      end
      ;-Slew
      6:begin
         obs_type = 'Slew'
         color0 = 0
         detfile0 = detfile0+'????_??/slew/??????/slew_??????_??h??m??s+???s.det.fits.gz'
      end
   endcase
   det = 0
   idlfile0 = testroot+'tab_cat_Neq1_HEASARC_'+strlowcase(obs_type)+'.idl'
   if keyword_set(results_only) then begin
      if file_test(idlfile0) then restore, idlfile0
      goto, no_get_dets
   endif
   detfile = file_search(detfile0,count=n_detfile)
   if n_detfile eq 0 then message, 'ERROR: detection files not found. '+detfile0
   det = 0
   for f=0L,n_detfile-1 do begin
      detfile1 = detfile[f]
      det1 = mrdfits(detfile1,1,h1,/silent)
;      w = where(det1.cent_snr ge (type le 4 ? snr_thresh:7.0),n_det1)
      w = where(det1.cent_snr ge snr_thresh,n_det1)
      if n_det1 eq 0 then continue
      det1 = det1[w]
      tags = tag_names(det1)
      n_tags = n_elements(tags)
      if (total(tags eq 'BKG_CELL') eq 0) and $
         (total(tags eq 'BKG_FIT' ) eq 0) then begin
         det0 = 0
         for i=0,n_det1-1 do begin
            det2 = create_struct(tags[0],det1[i].(0))
            for j=1,n_tags-1 do begin
               det2 = create_struct(det2,tags[j],det1[i].(j))
               if tags[j] eq 'BKG_VAR' then $
                  det2 = create_struct(det2,'BKG_CELL',0D,'BKG_FIT',0D)
            endfor
            det0 = (size(det0,/tname) eq 'STRUCT' ? [det0,det2] : [det2])
         endfor
         det1 = det0
         det0=0 & det2=0
      endif
      det = (size(det,/tname) eq 'STRUCT' ? [det,det1] : [det1])
   endfor
   no_get_dets:
   n_det = (size(det,/tname) eq 'STRUCT' ? n_elements(det) : 0)
   if n_det gt 0 then begin
      w = where(det.cent_snr ge snr_thresh, n_det)
      det = (n_det gt 0 ? det[w] : 0)
   endif
   print, 'Observation type: '+obs_type+'. Detections: '+strtrim(n_det,2)+$
          '. Reading time: '+strtime(systime(1)-t1)
   if n_det gt 0 then begin
      euler, det.glon_obj, det.glat_obj, ra, dec, select=2
      w = sort(ra)     ;Sort by RA
      det = det[w]
      ra = ra[w]
      dec = dec[w]
   endif
   n_src = n_det
   ;-Subtable header
   table0_tex = $
      tab + [$
      '%'+obs_type, $
      '\cutinhead{\small Observation type: '+obs_type+'}'] ;, $
;      subtable_header]
   table0_txt = $
      [obs_type, $
       tab+tab+tab+tab+tab+tab+tab+tab+tab+tab+tab+tab+tab+tab+tab+tab+tab+tab+tab+tab, $
       '#'+tab+'Name'+tab+'RA'+tab+'Dec'+tab+'Gal.lon.'+tab+'Gal.lat.'+tab+"r90[']"+tab+$
       'Obs.'+tab+'Exp[ks]'+tab+'CF[%]'+tab+'S/N(S)'+tab+'S/N(H)'+tab+'S/N(B)'+tab+$
       'Flux(S)'+tab+'Err.'+tab+'Flux(H)'+tab+'Err.'+tab+'Flux(B)'+tab+'Err.'$
       ;TEMP???
       +tab+'Nearest BAT source'+tab+"Offset[']"$
      ]
   ;-HEASARC tables
   i0 = n_elements(table0_txt) - 1
   for j=0,n_heasarc-1 do begin
      table0_txt[i0-1] = table0_txt[i0-1] + tab + tab + heasarc[j].table + tab
      table0_txt[i0] = table0_txt[i0] + tab+'real'+tab+'random'+tab+'sigma'
   endfor
   ;-Initialize HEASARC real and random match arrays
   heamatch_mask = (n_src gt 0 ? bytarr(n_src) : -1)
   if (n_src gt 0) and (n_heasarc gt 0) then begin
      heamatch_real = intarr(n_src,n_heasarc)
      heamatch_rnd  = fltarr(n_src,n_heasarc)
      heamatch_sig  = fltarr(n_src,n_heasarc)
      heacat = 0
   endif else begin
      heamatch_real = 0
      heamatch_rnd  = 0
      heamatch_sig  = 0
   endelse
;   ;-Set up Aitoff projection
;   map_set, 0, 0, 0, $
;            position=[0,0,normal[0],normal[1]], $ ;Normal coordinates
;            /aitoff, /isotropic, /noborder, /reverse, /grid, /noerase, $
;            /horizon, glinethick=thick, $
;            title='!5Observation type: '+obs_type, charsize=chsize
   ;-Loop over sources
   src_number = 0L
   n_src_plot = 0
   if n_src gt 0 then print, '   Looping over sources ('+$
                             strtrim(n_heasarc,2)+' catalogs): ', f='(a,$)'
   t2 = systime(1)
   for i=0,n_src-1 do begin
      t3 = systime(1)
      src = det[i]
      src_ra = ra[i]
      src_dec = dec[i]
      ra_hms = dms(src_ra,/hms)
      ra_hms[2] = round(10*ra_hms[2]/60D)
      if ra_hms[2] eq 10 then begin
         ra_hms[2] = 0
         ra_hms[1] = ra_hms[1] + 1
      endif
      if ra_hms[1] eq 60 then begin
         ra_hms[1] = 0
         ra_hms[0] = ra_hms[0] + 1
      endif
      if ra_hms[0] eq 24 then ra_hms[0] = 0
      dec_sign = '$'+(src_dec ge 0 ? '+':'-')+'$'
      dec_dm = intarr(2)
      dec_dm[0] = round(abs(src_dec))
      dec_dm[1] = round(60*(abs(src_dec)-floor(abs(src_dec))))
      if dec_dm[1] eq 60 then dec_dm[1] = 0
      name = 'BATSS J'+string(ra_hms[0], ra_hms[1], ra_hms[2], $
                              dec_sign,dec_dm[0], dec_dm[1], $
                              f='(2i02,".",i1,a,2i02)')
      exp_str = strtime(src.exposure,/table)
      if type le 2 then exp_str = strmid(exp_str,0,strpos(exp_str,'ks'))
      ie = (where(strtrim(src.eband,2) eq ebins.str))[0]
      src_snr = src.cent_snr
      src_rad = 2.32 * ((src_snr lt 5.46) * 4.94/(src_snr/4.0)^2.26 + $
                        ((src_snr ge 5.46) and (src_snr lt 8.26)) * 2.45/(src_snr/5.46)^1.13 + $
                        (src_snr ge 8.26) * 1.54/(src_snr/8.26)^0.26)
      src_flux = 1000D/Crabflux[ie]*src.cent_rate
      src_flux_err = src_flux / src_snr
      src_snr_str = strtrim(string(src_snr,f='(f7.2)'),2)
      src_flux_str = strtrim(string(src_flux,f='(f8.2)'))
      src_flux_err_str = strtrim(string(src_flux_err,f='(f8.2)'))
      ;-Skip if it matches an entry in the BAT Transient catalog
      offset = 60*angle([src_ra,src_dec], transpose([[trcat.ra],[trcat.dec]]))
      w = where(offset lt src_rad,n)
      if n ge 1 then begin
         ;print, 'Match: ', trcat[w].name+' '
         continue
      endif
      troffset0 = min(offset, w0) ;TEMP?
      trname0 = trcat[w0].name    ;TEMP?
      ;-Skip if it matches an entry in BAT GRB catalog
      offset = 60*reform(angle([src_ra,src_dec], transpose([[grb_all.ra],[grb_all.dec]])))
      w = where(offset lt src_rad,n)
      if n ge 1 then continue
      if min(offset) lt troffset0 then begin
         troffset0 = min(offset, w0)
         trname0 = grb_all[w0].name
      endif
      ;-Skip if it matches an entry in BATSS-only GRB catalog
      offset = 60*reform(angle([src_ra,src_dec], transpose([[grb_batss.ra],[grb_batss.dec]])))
      w = where(offset lt (src_rad+grb_batss.err_rad),n)
      if n ge 1 then continue
      if min(offset) lt troffset0 then begin
         troffset0 = min(offset, w0)
         trname0 = grb_batss[w0].name
      endif
      ;-Skip if MONTHLY or below and it overlaps with bad GTIs
      if type ge 2 then begin
         w = where((src.time lt gti_bad.stop) and $
                   (src.time_stop gt gti_bad.start),n)
         if n ge 1 then continue
      endif
;      ;-Skip if minimum offset is less than 10 arcmin
      if troffset0 lt 10 then continue
      ;-Set flag to include in table
      heamatch_mask[i] = 1B
      ;-Perform HEASARC search
      if n_heasarc eq 0 then goto, no_heamatch
      src_ra0 = src_ra
      src_dec0 = src_dec
      position = $
         string(dms(src_ra0,/hms),f='(3(i02,:," "))')+$
         ' '+(src_dec0 ge 0 ? '+':'-')+string(dms(abs(src_dec0)),f='(3(i02,:," "))')
      ;--Loop over HEASARC catalogs
      heacat0 = 0
      err_rad0 =  10. ;[arcmin] source error radius (TEMP?)
;      err_rad0 = (flag_r99 ? 1.42 : 1) * src_rad ;[arcmin]
      rad_inner = 1*60. ;[arcmin] inner annulus radius
      rad_outer = 3*60. ;[arcmin] outer annulus radius
      for j=0,n_heasarc-1 do begin
         table0 = heasarc[j].table
         ;--Loop over search radii
         for r=0,2 do begin
            case r of
               0:err_rad1 = err_rad0
               1:err_rad1 = rad_inner
               2:err_rad1 = rad_outer
            endcase
            radius = strtrim(string(err_rad1,f='(f6.2)'),2)
            tempfile = testroot+'HEASARC_catalog_temp_dahl.fits'
;            tempfile = testroot+'HEASARC_catalog_'+heasarc_table+$
;                       '_rnd'+strtrim(n_rnd,2)+'_temp.fits'
;            tempfile = testroot+'HEASARC_catalog_'+type+'_temp.fits'
;            tempfile = testroot+(strmid(heacat_suffix,1))_temp.fits'
            if table0 eq 'bzcat' then begin
               ;-Perform match to 'bzcat'
               offset = 60D * angle([src_RA0,src_Dec0], $
                                    transpose([[bzcat.RA],[bzcat.Dec]])) ;[arcmin]
               offset = reform(offset)
               w = where(offset le err_rad1, count)
               cat=0
               for k=0,count-1 do begin
                  cat0 = create_struct(bzcat[w[k]],'_OFFSET',offset[w[k]])
                  cat = (size(cat,/tname) eq 'STRUCT' ? [cat,cat0] : [cat0])
               endfor
               ;box0 = 2D     ;Size of 'box' to look for matches [deg]
               ;box = box0/[cos(src_dec*!dtor)>(box0/180D),1] ;[RA,Dec]
               ;ibox = where(((bzcat.RA gt src_RA0-box[0]) or $
               ;              (bzcat.RA gt src_RA0-box[0]+360D)) and $
               ;             ((bzcat.RA lt src_RA0+box[0]) or $
               ;              (bzcat.RA lt src_RA0+box[0]-360D)) and $
               ;             (bzcat.Dec gt src_Dec0-box[1]) and $
               ;             (bzcat.Dec lt src_Dec0+box[1]), n_box)
               ;if n_box gt 0 then begin
               ;   offset = 60D * angle([src_RA0,src_Dec0], $
               ;                        transpose([[bzcat[ibox].RA],$
               ;                                   [bzcat[ibox].Dec]])) ;[arcmin]
               ;   offset = reform(offset)
               ;   w = where(offset le err_rad1, count)
               ;   cat=0
               ;   for k=0,count-1 do begin
               ;      cat0 = create_struct(bzcat[ibox[w[k]]],'_OFFSET',offset[w[k]])
               ;      cat = (size(cat,/tname) eq 'STRUCT' ? [cat,cat0] : [cat0])
               ;   endfor
               ;endif else cat=0
               goto, no_browse_extract
            endif else begin
               spawn, 'browse_extract.pl table='+table0+$
                      ' position="'+position+'" radius='+radius+$
                      ' fields=ALL format=FITS resultmax=0'+$
                      ' outfile='+tempfile
               if file_test(tempfile) then begin
                  if not file_test(tempfile,/zero_length) then begin
                     unit = fxposit(tempfile,1,errmsg=errmsg)
                     if unit ge 0 then begin
                        free_lun, unit
                        cat = mrdfits(tempfile,1,hdr,/silent,ERROR_ACTION=0) ;TEMP???
                     endif else cat = 0
                  endif else cat = 0
                  spawn, 'rm '+tempfile
               endif else cat = 0
            endelse
            no_browse_extract:
            n_cat = (size(cat,/tname) eq 'STRUCT' ? n_elements(cat) : 0)
            case r of
               0:begin
                  n_real0 = n_cat
                  GOTO, NO_FIELDS
                  mask_boolean[j] = 1B
                  ;-Update HEACAT structure
                  tags = strlowcase(tag_names(cat))
                  case table0 of
                     'qorgcat':iname = (where(tags eq 'alt_name', count))[0]
                     'xtemaster':iname = (where(tags eq 'target_name', count))[0]
                     else:iname = (where(strpos(tags,'name') ge 0, count))[0]
                  endcase
                  if count eq 0 then $
                     message, 'ERROR: No NAME field in catalog '+table0+'. Revise'
                  iRA = (where(tags eq 'ra', count))[0]
                  if count ne 1 then $
                     message, 'ERROR: No RA field in catalog '+table0+'. Revise'
                  iDec = (where(tags eq 'dec', count))[0]
                  if count ne 1 then $
                     message, 'ERROR: No DEC field in catalog '+table0+'. Revise'
                  iOffset = (where(tags eq '_offset', count))[0]
                  if count ne 1 then $
                     message, 'ERROR: No OFFSET field in catalog '+table0+'. Revise'
                  heasarc_sortcol = strlowcase(strtrim(heasarc[j].sortcol,2))
                  sort_order = 1
                  if heasarc_sortcol ne '' then begin
                     if strmid(heasarc_sortcol,0,1) eq '-' then begin
                        sort_order = -1
                        heasarc_sortcol = strmid(heasarc_sortcol,1)
                     endif
                     isort = (where(tags eq heasarc_sortcol, count))[0]
                     if count ne 1 then $
                        message, 'ERROR: Sorting column '+heasarc_sortcol+$
                                 ' not found in catalog '+table0+'. Revise'
                  endif else isort = -1
                  heasarc_fields = strlowcase(strtrim(str_sep(heasarc[j].fields,string(9B)),2))
                  heasarc_filter = heasarc[j].filter
                  heacat1 = 0
                  n_cat0 = 0
                  for c=0,n_cat-1 do begin
                     if keyword_set(heasarc_filter) then begin
                        flag_filter = 0B
                        status = execute('flag_filter = cat[c].'+heasarc_filter)
                        if not status then message, 'Error in catalog filtering operation. Revise.'
                        if not flag_filter then continue
                     endif
                     name0 = strtrim(cat[c].(iname),2)
                     if (name0 eq '') and (table0 eq 'qorgcat') then name0 = cat[c].name
                     RA0  = cat[c].(iRA)
                     Dec0 = cat[c].(iDec)
                     offset0 = cat[c].(iOffset)
                     sortcol0 = (isort ge 0 ? cat[c].(isort) : 0)
                     case table0 of ;Get error radii [arcsec]
;                        'qorgcat': rad0=sqrt((15*0.1/cos(Dec0*!dtor))^2+(1.)^2)
;                        'veroncat':rad0=sqrt((15*0.1/cos(Dec0*!dtor))^2+(1.)^2)
;                        'nvss':    rad0=sqrt((cat[c].RA_error/cos(Dec0*!dtor))^2+$
;                                             (cat[c].Dec_error)^2)
                        else: rad0=0.
                     endcase
                     rad0 = rad0/60. ;[arcmin]
                     ;-Format fields
                     fields0 = ''
                     for f=0,n_elements(heasarc_fields)-1 do begin
                        if heasarc_fields[f] eq '' then continue
                        case heasarc_fields[f] of
                           'name': fields1=table0+': '+name0
                           'ra':   fields1=string(dms(RA0,/hms),f='(3(i02,:," "))')
                           'dec':  fields1=(Dec0 ge 0 ? '+':'-')+$
                                           string(dms(abs(Dec0)),f='(3(i02,:," "))')
                           'radius':fields1=string(rad0,f='(f6.3)')
                           'offset':fields1=string(offset0,f='(f6.3)')
                           else:begin
                              w = (where(tags eq heasarc_fields[f], count))[0]
                              if count ne 1 then $
                                 message, 'ERROR: Field "'+heasarc_fields[f]+$
                                          '" not found in catalog '+table0+'. Revise'
                              format = sxpar(hdr,'TDISP'+strtrim(w+1,2))
                              if size(format,/tname) ne 'STRING' then $
                                 format = sxpar(hdr,'TFORM'+strtrim(w+1,2))
                              format = '('+strlowcase(strtrim(format,2))+')'
                              fields1 = string(cat[c].(w), f=format)
                           end
                        endcase
                        fields0 = fields0 + (f eq 0 ? '':string(9B)) + fields1
                     endfor
                     heacat2 = {table:table0, name:name0, RA:RA0, Dec:Dec0, rad:rad0, $
                                offset:offset0, fields:fields0}
                     ;heacat2 = {index:i, table:table0, $
                     ;           name:name0, RA:RA0, Dec:Dec0, rad:rad0, offset:offset0,fields:fields0}
                     if size(heacat1,/tname) eq 'STRUCT' then begin
                        heacat1 = [heacat1, heacat2]
                        sortcol = [sortcol, sortcol0]
                     endif else begin
                        heacat1 = [heacat2]
                        sortcol = [sortcol0]
                     endelse
                     n_cat0 = n_cat0 + 1
                  endfor
                  ;-Sort according to SORTCOL, SORT_ORDER
                  heacat1 = heacat1[sort(sortcol)]
                  if sort_order lt 0 then $
                     heacat1 = heacat1[reverse(lindgen(n_elements(heacat1)))]
                  heacat0 = (size(heacat0,/tname) eq 'STRUCT' ? $
                             [heacat0,heacat1] : [heacat1])
                  NO_FIELDS:
               end
               1:n_inner = n_cat
               2:n_outer = n_cat
            endcase
         endfor
         n_rnd0 = (n_outer - n_inner) * (1-cos(!dtor*err_rad0/60)) / $
                  (cos(!dtor*rad_inner/60) - cos(!dtor*rad_outer/60)) ;Mean no. of matches within err_rad0
         n_rnd0 = n_rnd0 > 0D ;In the (wrong) case that N_OUTER < N_INNER
         prob_0 = exp(-n_rnd0) ;Poisson probability of 0 matches
         if n_real0 gt 0 then begin
            sigma0 =  sqrt(2) * inverf(prob_0)
         endif else begin
            sigma0 = -sqrt(2) * inverf(1-prob_0)
         endelse
         heamatch_real[i,j] = n_real0
         heamatch_rnd[i,j] = n_rnd0
         heamatch_sig[i,j] = sigma0
      endfor
;      if n_cat_tot gt 0 then begin
;         if r eq 0 then begin
;            heacat = (size(heacat,/tname) eq 'STRUCT' ? $
;                      [heacat,heacat0] : [heacat0])
;            heacat_src0 = heacat0
;         endif else begin
;            heacat1 = 0
;            for j=0,n_elements(heacat0)-1 do begin
;               heacat2 = create_struct(heacat0[j],'IRND',fix(r-1))
;               heacat1 = (size(heacat1,/tname) eq 'STRUCT' ? $
;                          [heacat1,heacat2] : [heacat2])
;            endfor
;            heacat_rnd = (size(heacat_rnd,/tname) eq 'STRUCT' ? $
;                          [heacat_rnd,heacat1] : [heacat1])
;         endelse
;      endif
      no_heamatch:
      ;-LaTeX Table entry
      src_number = src_number + 1
      table0_tex = $
         [table0_tex, $
          tab+[$
         strtrim(src_number,2)+amp+$
         name+amp+$
         string(src_ra,f='("$",f7.3,"$")')+amp+$
         string(src_dec,f='("$",f+7.3,"$")')+amp+$
         string(src.glon_obj,f='("$",f7.3,"$")')+amp+$
         string(src.glat_obj,f='("$",f+7.3,"$")')+amp+$
         ;string(60*src.err_rad,f='(f4.1)')+amp, $
         string(src_rad,f='(f4.1)')+amp, $
         '\url{'+src.obs_id+'}'+amp, $
         exp_str+amp+$
         string(100*src.pcodefr,f='(f5.1)')+amp, $
         (ie eq 0 ? '$'+src_snr_str+'$' : '')+amp+$
         (ie eq 1 ? '$'+src_snr_str+'$' : '')+amp+$
         (ie eq 2 ? '$'+src_snr_str+'$' : '')+amp+amp, $
         (ie eq 0 ? '$'+src_flux_str+'$'+amp+'$'+src_flux_err_str+'$' : '\multicolumn{2}{c}{}')+amp+$
         (ie eq 1 ? '$'+src_flux_str+'$'+amp+'$'+src_flux_err_str+'$' : '\multicolumn{2}{c}{}')+amp+$
         (ie eq 2 ? '$'+src_flux_str+'$'+amp+'$'+src_flux_err_str+'$' : '\multicolumn{2}{c}{}'), $
         ' \\']]
      ;-txt table entry
      name0 = str_sep(name,'$')
      name = name0[0]
      for j=1,n_elements(name0)-1 do name=name+name0[j]
      table0_txt = $
         [table0_txt, $
          strtrim(src_number,2)+tab+$
          name+tab+$
          string(src_ra,f='(f7.3)')+tab+$
          string(src_dec,f='(f+7.3)')+tab+$
          string(src.glon_obj,f='(f7.3)')+tab+$
          string(src.glat_obj,f='(f+7.3)')+tab+$
          ;string(60*src.err_rad,f='(f4.1)')+tab, $
          string(src_rad,f='(f4.1)')+tab+$
          src.obs_id+tab+$
          exp_str+tab+$
          string(100*src.pcodefr,f='(f5.1)')+tab+$
          (ie eq 0 ? src_snr_str : '')+tab+$
          (ie eq 1 ? src_snr_str : '')+tab+$
          (ie eq 2 ? src_snr_str : '')+tab+$
          (ie eq 0 ? src_flux_str+tab+src_flux_err_str : tab)+tab+$
          (ie eq 1 ? src_flux_str+tab+src_flux_err_str : tab)+tab+$
          (ie eq 2 ? src_flux_str+tab+src_flux_err_str : tab)$
          ;TEMP???
          +tab+trname0+tab+$
          strtrim(string(troffset0,f='(f6.1)'),2)$
         ]
;          ;HEASARC matches
;          +tab+strtrim(round(total(heamatch_real[i,*])),2)+tab+$
;          strtrim(string(rnd0,f='(f7.2)'),2)+tab+$
;          strtrim(string(rnd0_std,f='(f7.2)'),2)+tab+$
;          (rnd0_std eq 0 ? 'N/A':strtrim(string(sigma0,f='(f+7.2)'),2))+tab+$
;          (total(heamatch_real[i,*]) gt 0 ? heacat_src0[0].fields : '')$
;         ]
      ;-HEASARC matches
      i0 = n_elements(table0_txt) - 1
      for j=0,n_heasarc-1 do begin
         table0_txt[i0] = $
            table0_txt[i0] + $
            tab+strtrim(heamatch_real[i,j],2)+$
            tab+strtrim(string(heamatch_rnd[i,j],f='(f7.3)'),2)+$
            tab+strtrim(string(heamatch_sig[i,j],f='(f+7.3)'),2)
      endfor
      ;-Aitoff projection
      if troffset0 gt 6.0 then begin
         euler, src_ra, src_dec, src_glon, src_glat, select=1
         plots, src_glon, src_glat, psym=7, color=color0, $
                symsize=4-type/2.0, thick=(4-type/2.0)*thick
         n_src_plot = n_src_plot+1
      endif
      print, strtrim(src_number,2)+'('+strtime(systime(1)-t3)+') ', f='(a,$)'
      ;-Save results
      w = where(heamatch_mask)
      det0 = det  &  heamatch_real0 = heamatch_real
      heamatch_rnd0 = heamatch_rnd  &  heamatch_sig0 = heamatch_sig
      det = det[w]
      heamatch_real = heamatch_real[w,*]
      heamatch_rnd  = heamatch_rnd[w,*]
      heamatch_sig  = heamatch_sig[w,*]
      if not keyword_set(results_only) then begin
         save, det, heasarc_search, $
               heamatch_real, heamatch_rnd, heamatch_sig, $
               file=idlfile0
      endif
      det = det0  &  heamatch_real = heamatch_real0
      heamatch_rnd = heamatch_rnd0  &  heamatch_sig = heamatch_sig0
      det0=0 & heamatch_real0=0 & heamatch_rnd0=0 & heamatch_sig0=0
   endfor
   if n_src gt 0 then print, 'done('+strtime(systime(1)-t2)+')'
;   plot, [0], /nodata, color=255
   table = [table, table0_tex]
   table_txt = [table_txt, table0_txt, '']
   table0=0 & table0_txt=0 & cat=0
   if n_src_plot gt 0 then begin
      legend0 = {text:obs_type+' ('+strtrim(n_src_plot,2)+')  ', color:color0}
      legend = (size(legend,/tname) eq 'STRUCT' ? [legend,legend0] : [legend0])
   endif
endfor

;END OF TABLE
table_finish:
n = n_elements(table)
table = $
   [table[0:n-2], $
    tab+[$
   '\enddata'], $
;   '\tablenotetext{a}{\citet{baumgartner12}}', $
;   '\tablenotetext{b}{Results from \Swift-BAT 70-month survey}'], $
    '\end{deluxetable}', $
    '\clearpage', $
    '\end{landscape}']
;-Plot legend
legend, legend.text, color=legend.color, psym=7, thick=2*thick, $
        charsize=1.2, charthick=chthick, box=0, /bottom, /horizontal, $
        /normal, position=[0,0]

;Write output file
lun=0
openw,lun,texfile,/get_lun
printf, lun, table, f='(a)'
free_lun, lun
print, 'Closed output file:', '   '+texfile, f='(a)'
openw,lun,txtfile,/get_lun
printf, lun, table_txt, f='(a)'
free_lun, lun
print, 'Closed output file:', '   '+txtfile, f='(a)'
device, /close_file
print, 'Closed output file:', '   '+psfile, f='(a)'

END
