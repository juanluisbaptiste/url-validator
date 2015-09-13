#!/bin/bash

archivo_descarga="listado_pinf_ult.zip"
archivo="$1"
rm -f IXP.*

if [ "$archivo" == "" ]
then
    rm -f listado_pinf_ult.csv
    rm -f listado_pinf_ult.zip

    echo -e "No se ha especificado el archivo, descargando...\n"
    wget --user=netclean1212 --password=d5029ab925 http://www.ixp.net.co/Filter/$archivo_descarga
    unzip -P CCIT2014 $archivo_descarga
    archivo=$archivo_descarga
    #split -d -l 1000 $archivo mintic_ --additional-suffix=.txt    
fi    

extension="`echo $archivo | cut -d'.' -f2`"

if [  $extension == "zip" ]
then
    archivo_csv="`basename $archivo zip`csv"
else
    archivo_csv=$archivo
fi    

#iconv -f ISO-8859-1 -t utf-8 $archivo_csv > IXP.raw.utf8

#sort IXP.raw.utf8 | uniq | tee IXP.raw.utf8.sorted &>/dev/null
python urlvalidator.py -t -s $archivo_csv -d validas.txt -i invalidas.txt
#sort IXP.raw.utf8.sorted.ok | uniq | tee IXP.txt &>/dev/null

while read line
do           
	echo $line | sed -r 's/^.{7}// >> validas_sin_http.txt'
done < validas.txt