from BeautifulSoup import BeautifulSoup
import mechanize
from StringIO import StringIO
from PIL import Image
from CaptchaParser import CaptchaParser
import cookielib
import json
import sys, getopt
from clint.textui import colored, puts
from clint import arguments
import os
import ssl
import argparse


facultyInfo = []

# For SSL certificate error
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Progress Bar
def progress(count, total, status=''):
    rows, columns = os.popen('stty size', 'r').read().split()
    bar_len = int(columns) - 40

    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush() 

def login(regno, password):
    br = mechanize.Browser()
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    # For 403 Error
    br.set_handle_robots(False)
    cj = cookielib.CookieJar()
    br.set_cookiejar(cj)
    response = br.open('https://vtop.vit.ac.in/student/stud_login.asp')
    html = response.read()
    soup = BeautifulSoup(html)
    im = soup.find('img', id='imgCaptcha')
    image_response = br.open_novisit(im['src'])
    img = Image.open(StringIO(image_response.read()))
    parser = CaptchaParser()
    captcha = parser.getCaptcha(img)
    br.select_form('stud_login')
    br.form['regno'] = regno
    br.form['passwd'] = password
    br.form['vrfcd'] = str(captcha)
    br.submit()

    if (br.geturl() == 'https://vtop.vit.ac.in/student/home.asp'):
        puts(colored.yellow("LOGIN SUCCESSFUL"))
        return br
    else:
        print 'Could not login'
        return None


def parseFacultyPage(br, facultyID):
    if (br is None):
        return None

    br.open('https://vtop.vit.ac.in/student/stud_home.asp')
    response = br.open('https://vtop.vit.ac.in/student/official_detail_view.asp?empid=' + str(facultyID))
    html = response.read()
    soup = BeautifulSoup(html)
    tables = soup.findAll('table')

    # Extracting basic information of the faculty
    infoTable = tables[0].findAll('tr')
    name = infoTable[2].findAll('td')[1].text
    if (len(name) is 0):
        return None
    school = infoTable[3].findAll('td')[1].text
    designation = infoTable[4].findAll('td')[1].text
    room = infoTable[5].findAll('td')[1].text
    intercom = infoTable[6].findAll('td')[1].text
    email = infoTable[7].findAll('td')[1].text
    division = infoTable[8].findAll('td')[1].text
    additional_role = infoTable[9].findAll('td')[1].text

    # Parsing the open hours of the faculties
    openHours = []
    try:
        dayOne = infoTable[10].findAll('table')[0].findAll('tr')[1].findAll('td')[0].text
        dayTwo = infoTable[10].findAll('table')[0].findAll('tr')[2].findAll('td')[0].text
        startDayOne = infoTable[10].findAll('table')[0].findAll('tr')[1].findAll('td')[1].text
        startDayTwo = infoTable[10].findAll('table')[0].findAll('tr')[2].findAll('td')[1].text
        endDayOne = infoTable[10].findAll('table')[0].findAll('tr')[1].findAll('td')[2].text
        endDayTwo = infoTable[10].findAll('table')[0].findAll('tr')[2].findAll('td')[2].text
        openHours.append({'day': dayOne, 'start_time': startDayOne, 'end_time': endDayOne})
        openHours.append({'day': dayTwo, 'start_time': startDayTwo, 'end_time': endDayTwo})
    except IndexError:
        openHours = []

    outputPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    if os.path.isdir(outputPath) is False:
        os.makedirs(outputPath)
    result = {'empid': facultyID, 'name': name, 'school': school, 'designation': designation, 'room': room, 'intercom': intercom, 'email': email, 'division': division, 'open_hours': openHours}
    with open('output/' + str(facultyID) + '.json', 'w') as outfile:
        json.dump(result, outfile,indent=4)
    return result


def aggregate(regno, password):
    br = login(regno, password)
    if br is None:
        return
    skipped = 0
    successful = 0
    for i in range(10020, 20000, 1):
        result = parseFacultyPage(br, i)
        if (result is not None):
            facultyInfo.append(result)
            data = {'faculty_info': facultyInfo}
            with open('faculty_info.json', 'w') as outfile:
                json.dump(data, outfile,indent=4)
            successful += 1
        else:
            skipped += 1
        status = "%s Skipped, %s Succesful" % (skipped, successful)
        progress(i - 10020, 9980, status)

if __name__ == '__main__':
    print "-" * 40
    puts(colored.white(" " * 15 + "Faculty Information Scrapper"))
    print "-" * 40
    # argparse for better cmd arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("regno", help="Your Registration Number")
    parser.add_argument("password", help="Your Student Login Password")
    args = parser.parse_args()

    try:
        aggregate(args.regno, args.password)
    except Exception, e:
        print e
        if e.code==403:
            print 'Disallowed to access the page. Please check your internet connection.'
