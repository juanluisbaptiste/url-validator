rm -f listado_pinf_ult.csv
rm -f listado_pinf_ult.zip
wget --user=netclean1212 --password=d5029ab925 http://www.ixp.net.co/Filter/listado_pinf_ult.zip
unzip -P CCIT2014 listado_pinf_ult.zip
iconv -f ISO-8859-1 -t utf-8 listado_pinf_ult.csv > IXP.raw.utf8
sort IXP.raw.utf8 | uniq | tee IXP.raw.utf8.sorted
python parser.py
sort IXP.raw.utf8.sorted.ok | uniq | tee IXP.txt
