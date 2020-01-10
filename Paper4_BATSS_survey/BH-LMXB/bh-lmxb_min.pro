;08/09/19
;Report LEAST significant detections of BH-LMXBs

@/data/luna0/acopete/BATSS/pipeline/BATSS_general.pro

PRO BH_LMXB_MIN, $
   SRC_LIST                     ;Input - Source list

root = '/data/luna0/acopete/BATSS/' ;Root directory for BATSS data
dataroot = root+'Papers/Paper4_BATSS_survey/lc_battr/' ;Root directory for BAT TM LC data
datadir  = root+'Papers/Paper4_BATSS_survey/BH-LMXB/'  ;Write all output to working directory
if not file_test(datadir,/directory) then file_mkdir, dataroot

set_plot, 'PS'
!p.multi = [0, 1, 3]

;Initialize output TeX table
texfile = datadir+'tab_bh-lmxb_min.tex'
tab = string(9B)
table = $
   ['%LaTeX table with least significant BATSS detections confirmed BH-LMXBs', $
    '', $
    '%\begin{longrotatetable}', $
    '%\renewcommand{\arraystretch}{1.10}', $
    '%\renewcommand{\tabcolsep}{0.4em}', $
    '%\tabletypesize{\scriptsize}', $
    '\tablecolumns{10}', $
    '', $
    '\begin{deluxetable*}{r l r r c r r c r r}', $
    tab+'%Preamble', $
    tab+'\tablecaption{Least significant BATSS detections of confirmed BH-LMXBs', $
    tab+tab+'\label{tab:BH-LMXBs}}', $
    tab+'\tablehead{', $
    tab+tab+'\colhead{\multirow{2}{*}{\#}} &', $
    tab+tab+'\colhead{\multirow{2}{*}{Name}} &', $
    tab+tab+'\multicolumn{2}{c}{Orbital} & &', $
    tab+tab+'\multicolumn{2}{c}{Daily} & &', $
    tab+tab+'\multicolumn{2}{c}{Weekly} \\', $
    tab+tab+'\cline{3-4} \cline{6-7} \cline{9-10}', $
    tab+tab+' & &', $
    tab+tab+'\colhead{S/N ($E_\textrm{band}$)} & ', $
    tab+tab+'\colhead{Obs. ID} & & ', $
    tab+tab+'\colhead{S/N ($E_\textrm{band}$)} & ', $
    tab+tab+'\colhead{Obs. ID} & & ', $
    tab+tab+'\colhead{S/N ($E_\textrm{band}$)} & ', $
    tab+tab+'\colhead{Obs. ID} & ', $
    tab+'}', $
    tab+'%Table data', $
    tab+'\startdata']

n_src = n_elements(src_list)
for i=0,n_src-1 do begin
   src = src_list[i]
   line = tab + strtrim(i+1,2)+' & '+src
   idlfile = dataroot+'lc_raw/'+src+'.lc.idl'
   restore, idlfile
   PSfile = datadir+src+'_hist.ps'
   device, filename=PSfile, $ ;/color, bits_per_pixel=8, filename=PSfile, $
           /portrait, xoffset=0.2, yoffset=0.2, xsize=8.1, ysize=10.6, /inches
   for j=0,2 do begin
      case j of
         0: begin
            lc_type = 'Orbital'
            lc = lc_batss_orbital
         end
         1: begin
            lc_type = 'Daily'
            lc = lc_batss_daily
         end
         2: begin
            lc_type = 'Weekly'
            lc = lc_batss_weekly
         end
      endcase
      snr_min = min(lc.cent_snr, imin0)
      min_eband = imin0 mod 3
      imin = imin0 / 3
      min_obsid = lc[imin].obs_id
      case min_eband of
         0:min_eband_str = 'S'
         1:min_eband_str = 'H'
         2:min_eband_str = 'B'
      endcase
      line += ' & '+string(snr_min,f='(f6.2)')+' ('+min_eband_str+') & '+$
              '\nolinkurl{'+min_obsid+'}'+(j eq 2 ? '' : ' & ')
      plothist, lc.cent_snr[min_eband], title=src+': '+lc_type+' detection S/N ('+min_eband_str+')'
      oplot, snr_min*[1,1], [0,700], linestyle=2
      ;legend, 'Sigma = '+string(stddev(lc.cent_snr[min_eband]),f='(f5.3)')
   endfor
   line += (i lt n_src-1 ? ' \\' : '')
   table = [table, line]
   device, /close_file
endfor

;Close and write table TeX file
table = $
   [table, $
    tab+'\enddata', $
    '\end{deluxetable*}', $
    '%\end{longrotatetable}']
openw, lun, texfile, /get_lun
printf, lun, table, f='(a)'
free_lun, lun

END
