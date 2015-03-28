from bs4 import BeautifulSoup
import mechanize
from StringIO import StringIO
from PIL import Image
from CaptchaParser import CaptchaParser
import cookielib
import json

REGNO = ''
PASSWORD = ''

def login():
	br = mechanize.Browser()
	br.set_handle_redirect(True)
	br.set_handle_referer(True)
	cj = cookielib.CookieJar()
	br.set_cookiejar(cj)
	response = br.open('https://academics.vit.ac.in/student/stud_login.asp')
	html = response.read()
	soup = BeautifulSoup(html)
	im = soup.find('img', id='imgCaptcha')
	image_response = br.open_novisit(im['src'])
	img = Image.open(StringIO(image_response.read()))
	parser = CaptchaParser()
	captcha = parser.getCaptcha(img)
	br.select_form('stud_login')
	br.form['regno'] = REGNO
	br.form['passwd'] = PASSWORD
	br.form['vrfcd'] = str(captcha)
	br.submit()
	if(br.geturl() == 'https://academics.vit.ac.in/student/home.asp'):
		print '-'*30
		print ' '*12+'SUCCESS'
		print '-'*30
		return br
	else:
		return None

def parseFacultyPage(facultyID):
	br = login()
	if(br is None):
		return None

	br.open('https://academics.vit.ac.in/student/stud_home.asp')
	response = br.open('https://academics.vit.ac.in/student/official_detail_view.asp?empid=' + str(facultyID))
	html = response.read()
	soup = BeautifulSoup(html)
	tables = soup.findAll('table')
	
	#Extracting basic information of all the faculty
	infoTable = tables[1].findAll('tr')
	name = infoTable[1].findAll('td')[1].text
	school = infoTable[2].findAll('td')[1].text
	designation = infoTable[3].findAll('td')[1].text
	room = infoTable[4].findAll('td')[1].text
	intercom = infoTable[5].findAll('td')[1].text
	email = infoTable[6].findAll('td')[1].text
	division = infoTable[7].findAll('td')[1].text
	additional_role = infoTable[8].findAll('td')[1].text

	#Parsing the open hours of the faculties
	dayOne = infoTable[9].findAll('table')[0].findAll('tr')[1].findAll('td')[0].text
	dayTwo = infoTable[9].findAll('table')[0].findAll('tr')[2].findAll('td')[0].text
	startDayOne = infoTable[9].findAll('table')[0].findAll('tr')[1].findAll('td')[1].text
	startDayTwo = infoTable[9].findAll('table')[0].findAll('tr')[2].findAll('td')[1].text
	endDayOne = infoTable[9].findAll('table')[0].findAll('tr')[1].findAll('td')[2].text
	endDayTwo = infoTable[9].findAll('table')[0].findAll('tr')[2].findAll('td')[2].text

	openHours = []
	openHours.append({'day': dayOne, 'start_time': startDayOne, 'end_time': endDayOne})
	openHours.append({'day': dayTwo, 'start_time': startDayTwo, 'end_time': endDayTwo})

	result = {'name': name, 'school': school, 'designation': designation, 'room': room, 'intercom': intercom, 'email': email, 'division': division, 'open_hours': openHours}
	return result

result = parseFacultyPage(10395)
print json.dumps(result)
