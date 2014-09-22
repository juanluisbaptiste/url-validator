sort listado_pinf_ult.csv | uniq | tee IXP.raw.sorted | iconv -c -f ASCII -t ASCII > IXP.raw.sorted.ascii
