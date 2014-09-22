#! /usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import pycurl
import datetime
import time
import smtplib
import re
import urlparse
import string
import urllib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def is_valid_url(urls):
    regex = re.compile(
        r'^http://'  # http://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.? | '  # dominio...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?:/?|[/?]\S+)$', re.VERBOSE | re.IGNORECASE)
    if(urls is not None and regex.search(urls) is None):
        return urls


def joinUrls(n,m):
    return n+m


def saveFile(archivo,contenido):
        arch = open(archivo, 'aw')
        arch.write(contenido + '\r\n')
        arch.close()


def sendAdminMail(totalUrls, urlsOk, urlsBad, totalTime, archOk, archBad):
    sender = 'adm.python111@gmail.com'
    passSender = '12blockyou34'
    receiver = 'hdominguez@apukaysecurity.com'
    #Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Ejecucion script filtro de URLs"
    msg['From'] = sender
    msg['To'] = receiver

    text = "Hi!\nHow are you?\n"
    html = """<div>Estimado SysAdmin,<br />Le informamos que el script para validar URLs p&aacute;ginas pornogr&aacute;ficas se ha ejecutado exitosamente. <br />
    A continuaci&oacute;n los resultados obtenidos:</div>"""
    html = html + "<ul>"
    html = html + "<li type='disc'><span> Total Urls procesadas:    {0}</span></li>".format(totalUrls)
    html = html + "<li type='disc'><span> Total Urls Ok:    {0}</span></li>".format(urlsOk)
    html = html + "<li type='disc'><span> Total Urls Bad:    {0}</span></li>".format(urlsBad)
    html = html + "<li type='disc'><span> Tiempo transcurrido (segundos):    {0}</span></li>".format(totalTime)
    html = html + "<li type='disc'><span> Archivo Ok generado:    {0}</span></li>".format(archOk)
    html = html + "<li type='disc'><span> Archivo Bad generado:    {0}</span></li>".format(archBad)
    html = html + "</ul>"
    html = html + "Saludos cordiales,"
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)
    errstr = ""

    try:
        smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
        smtpObj.ehlo()
        smtpObj.starttls()
        smtpObj.ehlo
        smtpObj.login(sender, passSender)
        smtpObj.sendmail(sender, receiver, msg.as_string())
        smtpObj.close()
    except Exception, errstr:
        raise smtplib.SMTPException, errstr
        print errstr    


try:
    import signal
    from signal import SIGPIPE, SIG_IGN
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
except ImportError:
    pass


#threads
num_conn = 50

caracteresNoPermitidos = {' ' : '', '"' : '', '<' : '', '>' : '', '^' : '', '`' : '', '{' : '', '|' : '', '}' : '',
                          '€' : '', '‚' : '', 'ƒ' : '', '„' : '', '…' : '', '†' : '', '‡' : '', 'ˆ' : '', '‰' : '',
                          'Š' : '', '‹' : '', 'Œ' : '', 'Ž' : '', '‘' : '', '’' : '', '“' : '', '”' : '', '•' : '',
                          '–' : '', '—' : '', '˜' : '', '™' : '', 'š' : '', '›' : '', 'œ' : '', 'ž' : '', 'Ÿ' : '',
                          '¡' : '', '¢' : '', '£' : '', '¥' : '', '|' : '', '§' : '', '¨' : '', '©' : '', 'ª' : '',
                          '«' : '', '¬' : '', '¯' : '', '®' : '', '¯' : '', '°' : '', '±' : '', '²' : '', '³' : '',
                          '´' : '', 'µ' : '', '¶' : '', '·' : '', '¸' : '', '¹' : '', 'º' : '', '»' : '', '¼' : '',
                          '½' : '', '¾' : '', '¿' : '', 'À' : '', 'Á' : '', 'Â' : '', 'Ã' : '', 'Ä' : '', 'Å' : '',
                          'Æ' : '', 'Ç' : '', 'È' : '', 'É' : '', 'Ê' : '', 'Ë' : '', 'Ì' : '', 'Í' : '', 'Î' : '',
                          'Ï' : '', 'Ð' : '', 'Ò' : '', 'Ó' : '', 'Ô' : '', 'Õ' : '', 'Ö' : '', 'Ø' : '', 'Ù' : '',
                          'Ú' : '', 'Û' : '', 'Ü' : '', 'Ý' : '', 'Þ' : '', 'ß' : '', 'à' : '', 'á' : '', 'â' : '',
                          'ã' : '', 'ä' : '', 'å' : '', 'æ' : '', 'ç' : '', 'è' : '', 'é' : '', 'ê' : '', 'ë' : '',
                          'ì' : '', 'í' : '', 'î' : '', 'ï' : '', 'ð' : '', 'ò' : '', 'ó' : '', 'ô' : '', 'õ' : '',
                          'ö' : '', '÷' : '', 'ø' : '', 'ù' : '', 'ú' : '', 'û' : '', 'ü' : '', 'ý' : '', 'þ' : '',
                          'ÿ' : '' }


urls = open('/var/www/html/apukaysecurity/download/IXP.raw.utf8.sorted', 'r')
lineas = urls.readlines()
urls.close()


fecha = datetime.date.today()
fecha = fecha.strftime("%d%m%Y")
archOk = "IXP.raw.utf8.sorted.ok" #+ str(fecha)    #nombre archivo URLs procesadas con formato valido con y sin conexion exitosa
archBad = "urllistBad" #+ str(fecha)  #nombre archivo URLs invalidas/sin conexion
counter = 0     #total de urls validas procesadas
ok = 0          #urls con conexion exitosa
bad = 0         #urls sin conexion exitosa


#clear enters
lineas = [x.strip() for x in lineas]

#validate URL format
for li in lineas:
    invalidLines = is_valid_url('http://' + li)
    if invalidLines is not None:
        saveFile("/var/www/html/apukaysecurity/download/" + archBad, " Invalid url  --->  " + li)

#removing final "/" character
lineas = [re.sub('/$', '', x) for x in lineas]

# creamos una expresion regular desde el diccionario de caracteresNoPermitidos
regex = re.compile("(%s)" % "|".join(map(re.escape, caracteresNoPermitidos.keys())))

urlsDomain = []      #dominio de la url
urlsResto = []       #path y query de la url
urlsComplete = []    #urlsDomain[] + urlsResto[]

for li in lineas:
    #liNew = "http://" + li
    liNew = li
    parsedUrl = urlparse.urlparse(liNew)    
    urlsDomain.append(regex.sub(lambda x: str(caracteresNoPermitidos[x.string[x.start() :x.end()]]), parsedUrl.netloc))
    urlsResto.append(parsedUrl.path + parsedUrl.query)

urlsComplete = map(joinUrls, urlsDomain, urlsResto)

#removing duplicate entries
urlsComplete = sorted(set(urlsComplete))


queue = []
for url in urlsComplete:
    url = url.strip()
    if not url or url[0] == "#":
        continue
    queue.append(url)


assert queue, "no URLs given"
num_urls = len(queue)
num_conn = min(num_conn, num_urls)
assert 1 <= num_conn <= 10000, "Invalid number of concurrent connections"

time1 = time.time()

m = pycurl.CurlMulti()
m.handles = []
for i in range(num_conn):
    c = pycurl.Curl()
    c.fp = None

    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.MAXREDIRS, 30)
    c.setopt(pycurl.CONNECTTIMEOUT, 40)
    c.setopt(pycurl.TIMEOUT, 40)
    c.setopt(pycurl.CONNECT_ONLY, 1)
    c.setopt(pycurl.NOSIGNAL, 1)
    m.handles.append(c)


# Main loop
freelist = m.handles[:]
num_processed = 0

while num_processed < num_urls:
    # If there is an url to process and a free curl object, add to multi stack
    while queue and freelist:
        url = queue.pop(0)
        c = freelist.pop()
        c.setopt(pycurl.URL, 'http://' + url)
        m.add_handle(c)
        c.url = url

    # Run the internal curl state machine for the multi stack
    while 1:
        ret, num_handles = m.perform()
        #time.sleep(1)
        if ret != pycurl.E_CALL_MULTI_PERFORM:
            break

    # Check for curl objects which have terminated, and add them to the freelist
    while 1:
        num_q, ok_list, err_list = m.info_read()
        for c in ok_list:
            counter = counter + 1
            ok = ok + 1
            m.remove_handle(c)
            #print "Success:[", counter, "]", c.url
	    xurl = c.url
            #saveFile("/var/www/html/apukaysecurity/download/" + archOk, " ---->" + c.url)
            saveFile("/var/www/html/apukaysecurity/download/" + archOk, xurl.replace('http://',''))
            freelist.append(c)
        for c, errno, errmsg in err_list:
            counter = counter + 1
            bad = bad + 1
            m.remove_handle(c)
            #print "Failed:[", counter, "]", c.url, errno, errmsg
              #saveFile("/var/www/html/apukaysecurity/download/" + archOk, c.url)
            xurl = c.url
            saveFile("/var/www/html/apukaysecurity/download/" + archOk, xurl.replace('http://',''))
            #saveFile("/var/www/html/apukaysecurity/download/" + archBad, str(errno)  + " ---> " + errmsg  + " ---> " +  c.url)
            saveFile("/var/www/html/apukaysecurity/download/" + archBad, str(errno)  + " ---> " + errmsg  + " ---> " +  xurl.replace('http://',''))
            freelist.append(c)
        num_processed = num_processed + len(ok_list) + len(err_list)
        if num_q == 0:
            break

    # Currently no more I/O is pending, could do something in the meantime
    # (display a progress bar, etc.).
    # We just call select() to sleep until some more data is available.
    m.select(1.0)


# Cleanup
for c in m.handles:
    if c.fp is not None:
        c.fp.close()
        c.fp = None
    c.close()
m.close()

time2 = time.time()
totaltime = time2 - time1
totaltime = round(totaltime, 3)
sendAdminMail(str(counter), str(ok), str(bad), str(totaltime), archOk, archBad)
