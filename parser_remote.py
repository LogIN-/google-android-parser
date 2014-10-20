import sys, os, shutil, re, hashlib, MySQLdb, codecs, hashlib, time, datetime, urllib2, random
from urllib2 import URLError
from urllib import unquote
from dateutil import parser
from BeautifulSoup import BeautifulSoup


comAppPat = re.compile(r'<link rel="canonical" href="/app/.+/([^"]+)">')
comAppNamePat1 = re.compile("<h1 class=\"item\"><img .*/>\n<span class=\"fn\">(.*)</span> </h1>",re.UNICODE|re.DOTALL)
comAppNamePat2 = re.compile("<h1><img .*/>([^\"]+) </h1>",re.UNICODE|re.DOTALL)
iconPat = re.compile("<h1 ?[^<]+<img src=\"(.*)\" style=\"float:left;margin-right:10px\"",re.UNICODE|re.DOTALL)
sizePat = re.compile(r'<span>(\d+) kb</span>')
#verPat = re.compile(r'Latest version: +(\d+\.?\d*)[\D]*(\d+\.?\d*)')    ##[0-9]+(?:\.[0-9]*)?
verPat = re.compile("Latest version: (.*) \(for Android version (.*) and higher(, supports App2SD)?\)",re.UNICODE|re.DOTALL)
varPat1 = re.compile("Latest version: (.*) \(for all Android versions(, supports App2SD)?\)",re.UNICODE|re.DOTALL)
#categPat = re.compile(r'&#187; <a href="/apps/[^/]+/([^"]+)"')
categPat = re.compile("&#187; <a href=\"/apps/[^/]+/[^/]+\">(.*)</a> &#187;",re.UNICODE|re.DOTALL)
devPat = re.compile(r'<a href="/browse/dev/([^"]+)"')
cPat = re.compile(r'\\\"(([a-zA-Z0-9._-])+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4})\\\"')
pgp = re.compile(r'permission-group\.(\w+)\\')
pp = re.compile(r'permission\.(\w+)\\')
relatedComIdPat = re.compile(r'/app/([^"]+)/([^"]+)')
youtubePat = re.compile(r'http://www.youtube.com/embed/([\w\d]+)\?wmode=opaque')
jsPat = re.compile("window.pageData = \"(.*)\";",re.UNICODE|re.DOTALL)
officialPat = re.compile("android.permission.*((?:(?:https?|ftp):\/\/|www\.)[-a-z0-9+&@#\/%?=~_|!:,.;]*[-a-z0-9+&@#\/%=~_|])",re.UNICODE|re.DOTALL)
freePat = re.compile("<span class=('|\")priceFree('|\")>([^\"]+)</span>",re.UNICODE|re.DOTALL)
floatPat = re.compile(r'(\d+.?\d+)',re.UNICODE|re.DOTALL)
verNumbPat = re.compile(r'([\d\.]+)',re.UNICODE|re.DOTALL)

AndmMrkComPath = re.compile(r'<span class="count">([\d\.]+)</span>',re.UNICODE|re.DOTALL)

conn = MySQLdb.connect(host= "127.0.0.1",
	use_unicode = True, 
	charset = "utf8",
	user="android_bulk",
	passwd="android_bulk",
	db="android_bulk")

cursor = conn.cursor()
cursor.execute(r"SET NAMES utf8;")

def main(argv):
	
	if (len(sys.argv) > 1):
		
		url = sys.argv[1]
		#req = urllib2.Request(url)
		tempname = str(random.randrange(0, 101, 2))
		tempfilename = "/home/login/Desktop/parser/html/"+tempname+".html"
		#try:
		os.system("wget --output-document="+tempfilename+" " + url)
		convert_to_utf8(tempfilename)
		
		try:
			file = codecs.open(tempfilename, "r", "utf-8" )
			html = file.read()
			pageData = PageData(html)
		except IOError:
			try:
				file = codecs.open(tempfilename + ".bak", "r", "utf-8" )
				html = file.read()
				pageData = PageData(html)
			except IOError:
				print 'Cannot open file 2'
		
		#r = urllib2.urlopen(req)
		#content = r.read()
		#encoding = r.headers['content-type'].split('charset=')[-1]
		#content = unicode(content, encoding)			
		#html = unicode(content).encode('utf-8')
		
		#pageData = PageData(html)
	#except URLError, e:
		#print e.reason

		conn.close()
		os.remove(tempfilename)
		os.remove(tempfilename + ".bak")
	else:
		print "No URL"
		
def convert_to_utf8(filename):
    # gather the encodings you think that the file may be
    # encoded inside a tuple
    encodings = ('windows-1253', 'iso-8859-7', 'macgreek')

    # try to open the file and exit if some IOError occurs
    try:
        f = open(filename, 'r').read()
    except Exception:
        sys.exit(1)

    # now start iterating in our encodings tuple and try to
    # decode the file
    for enc in encodings:
        try:
            # try to decode the file with the first encoding
            # from the tuple.
            # if it succeeds then it will reach break, so we
            # will be out of the loop (something we want on
            # success).
            # the data variable will hold our decoded text
            data = f.decode(enc)
            break
        except Exception:
            # if the first encoding fail, then with the continue
            # keyword will start again with the second encoding
            # from the tuple an so on.... until it succeeds.
            # if for some reason it reaches the last encoding of
            # our tuple without success, then exit the program.
            if enc == encodings[-1]:
                sys.exit(1)
            continue

    # now get the absolute path of our filename and append .bak
    # to the end of it (for our backup file)
    fpath = os.path.abspath(filename)
    newfilename = fpath + '.bak'
    # and make our backup file with shutil
    shutil.copy(filename, newfilename)

    # and at last convert it to utf-8
    f = open(filename, 'w')
    try:
        f.write(data.encode('utf-8'))
    except Exception, e:
        print e
    finally:
        f.close()

class PageData:
	def __init__(self, html):		

		##############DEVELOPER##############
		self.developer = ""
		self.developerUsername = ""
		self.officialPage = ""
		self.contact = ""
		self.password = ""
		self.emailsalt = ""
		self.usercreated = ""
		self.userID = ""
		self.userProfileID = ""
		self.userLogo = ""
		##############CATEGORY###############
		self.categoryID = ""
		self.categ = ""
		##############APPLICATION###############
		self.appHash = ""
		self.comAppName = ""
		self.appName = ""
		self.appID = ""			
		self.screenshots = []
		self.desc = ""		
		self.android_version = ""
		self.app2sd = ""				
		self.permissions = []
		self.permGroupID = ""
		self.permPermID = ""
		self.priceFree = ""
		self.pricePaid = ""
		self.price = ""		
		self.MetaoperatingSystems = ""		
		self.Metaimage = "0"
		self.icon = ""
		self.MetaratingValue = "0"
		self.rating = ""
		self.Metavotes = "0"
		self.votes = ""
		self.MetadatePublished = "0"
		self.added = ""	
		self.MetasoftwareVersion = "0"
		self.version = ""		
		self.MetanumDownloads = "0"
		self.installs = ""
		self.MetafileSize = "0"
		self.size = ""		
		self.youtube = ""
		self.related = ""
		self.relatedAppHash = ""
		self.AndmMrkCom = "0"
		
		
		try:
			self.soup = BeautifulSoup(html)
			self.marketcomments = Comments(self.soup)
		except Exception, e:
			print e
			return

		
		############## DEVELOPER 1. INSERT ##############
		# Contact
		cMatch = cPat.search(html)
		if cMatch:
			self.contact = unicode(cMatch.group(1)).encode('utf-8')			
			self.developerUsername = unicode(cMatch.group(2)).encode('utf-8')			
			self.password = hashlib.sha512(self.contact).hexdigest()
			self.emailsalt = hashlib.md5(self.contact).hexdigest()

		else:
			self.contact = str(time.time()) + "@email.com"
			self.password = hashlib.sha512("DevElOpeR").hexdigest()
			self.emailsalt = hashlib.md5("unknown@email.com").hexdigest()
			self.developerUsername = str(time.time())[-2:]
			
		# Developer
		devMatch = devPat.search(html)
		if devMatch:
			self.developer = unicode(devMatch.group(1)).encode('utf-8')
			self.developerUsername += self.developer
			devCheck = 1
		else:
			self.developer = str(time.time()) + "NONE"
			self.developerUsername = str(time.time()) + "NONE"
			devCheck = 0
			
		if self.emailsalt != "6b08a0d645c12fdaf167c5b54436338b":
			self.developerUsername = self.contact
		elif devCheck != 0 and self.emailsalt == "6b08a0d645c12fdaf167c5b54436338b":
			self.developerUsername = self.developerUsername
				
		# OfficialPage		
		jsMatch = jsPat.search(html)
		if jsMatch:		
			offMatch = officialPat.search(jsMatch.group(1))
			if offMatch:
				self.officialPage = offMatch.group(1)
			else:
				self.officialPage = "NONE"
		else:
			self.officialPage = "NONE"
				
		self.usercreated = time.strftime('%Y-%m-%d %H:%M:%S')
		self.userLogo = hashlib.md5("DEFAULT").hexdigest()

		############## DEVELOPER INSERT  ###################
		try:
			cursor.execute(r"""SELECT user_id  FROM `users` WHERE `user_username` = %s LIMIT 1;""",(self.developerUsername))
			
			if cursor.rowcount == 0:
				try:
					cursor.execute(r"""INSERT IGNORE INTO `android_bulk`.`users` 
					(`user_id`, `user_type`, `user_username`, `user_password`, `user_email`, `user_verified`, `user_salt`, `user_lastIP`, `user_created`, `user_accessed`) VALUES 
					(NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",('6', self.developerUsername, self.password, self.contact, '0', self.emailsalt, '1308875047', self.usercreated, self.usercreated,))
					conn.commit()
					self.userID = cursor.lastrowid
					if self.userID != "":
						try:										
							cursor.execute(r"""INSERT IGNORE INTO `android_bulk`.`users_profile` 
							(`user_prof_id`, `user_prof_guid`, `user_prof_name`, `user_prof_surname`, `user_prof_country`, `user_prof_city`, `user_prof_age`, `user_prof_gender`, `user_prof_postal_code`, `user_prof_address`, `user_prof_phone`, `user_prof_mobile`, `user_prof_web`, `user_prof_logo`, `user_prof_devices`, `user_prof_payment_type`, `user_prof_earned`) VALUES 
							(NULL, %s, %s, '0', '0', '0', '0', '0', '0', '0', '0', '0',  %s, %s, 'NULL', '0', '0');""",(self.userID, self.developer, self.officialPage, self.userLogo))
							conn.commit()
							self.userProfileID = cursor.lastrowid
							
						except MySQLdb.Error, e:
							print "Error %d: %s" % (e.args[0], e.args[1])
					else:
						return
							
				except MySQLdb.Error, e:
					print "Error %d: %s" % (e.args[0], e.args[1])
					return
			else:
				self.userID = cursor.fetchone()[0]
		except MySQLdb.Error, e:
			print "Error %d: %s" % (e.args[0], e.args[1])
			return
		############## DEVELOPER END ###################
		
		############## CATEGORY 2. INSERT ##############
		# Category
		categMatch = categPat.search(html)
		if categMatch:
			self.categ = unicode(categMatch.group(1)).encode('utf-8')
			self.categ = self.unquote_u(self.categ)
		else:
			self.categ = "Uncategorised"	
		
		try:
			cursor.execute(r"""SELECT cat_id FROM `list_categories` WHERE `cat_name` = %s LIMIT 1;""",(self.categ))
			
			if cursor.rowcount == 0:
				try:
					cursor.execute(r"""INSERT INTO `android_bulk`.`list_categories` (`cat_id`, `cat_parent`, `cat_name`) VALUES 
								(NULL, (SELECT MAX(cat_id+1) FROM `list_categories` as maxid), %s)""",(self.categ))
					conn.commit()
					self.categoryID = cursor.lastrowid
					
				except MySQLdb.Error, e:
					print "Error %d: %s" % (e.args[0], e.args[1])
			else:
				self.categoryID = cursor.fetchone()[0]
					
		except MySQLdb.Error, e:
			print "Error %d: %s" % (e.args[0], e.args[1])
			
		############## CATEGORY 2. END ###################
		
		############## APPLICATION 3.INSERT ##############		
		#Com App Name & Hash
		comAppName = comAppPat.search(html)
		if comAppName:
			self.comAppName = unicode(comAppName.group(1)).encode('utf-8')
			self.appHash = hashlib.md5(self.comAppName).hexdigest()
		else:
			print "#####***No ComApp Name!***#####"
			return
		print "*******************************"
		print self.comAppName
		
		##### Catch Meta Values
		self.CatchMeta()
		
		# App Name
		appNameMatch = comAppNamePat1.search(html)
		if appNameMatch:
			self.appName = unicode(appNameMatch.group(1)).encode('utf-8')
		else:
			appNameMatch = comAppNamePat2.search(html)
			if appNameMatch:
				self.appName = unicode(appNameMatch.group(1)).encode('utf-8')
			else:
				self.appName = "NONE"
						
		# App Info => INSTALLS, VOTES, RATING, SIZE
		appInfo = self.soup.find('div', attrs={'class': 'appInfo'})
		
		if appInfo:	
			if self.MetanumDownloads == "0":
				installsElem = appInfo.find('b')
				if installsElem: 
					self.installs = unicode(installsElem.string).encode('utf-8')
					if self.installs == "" or self.installs == None:
						self.installs = "0"
				else:
					self.installs = "0"
			else:
				self.installs = self.MetanumDownloads				
			
			if self.Metavotes == "0":
				votes = appInfo.find('span', attrs={'class': 'votes'})
				if votes: 
					self.votes = unicode(votes.string).encode('utf-8')
					if self.votes == "" or self.votes == None:
						self.votes = "0"
				else:
					self.votes = "0"
			else:
				self.votes = self.Metavotes
			
			if self.MetaratingValue == "0":
				rating = appInfo.find('span', {'class': 'rating'})
				if rating: 
					self.rating = unicode(rating.string).encode('utf-8')
					if self.rating == "" or self.rating == None:
						self.rating = "0"
				else:
					self.rating = "0"
			else:
				self.rating = self.MetaratingValue
		
		if self.MetafileSize == "0":
			sizeMatch = sizePat.search(html)
			if sizeMatch:
				self.size = unicode(sizeMatch.group(1)).encode('utf-8')
				if self.size == "" or self.size == None:
					self.size = "0"
			else:
				self.size = "0"
		else:
			self.size = self.MetafileSize

		# Description
		appDesc = self.soup.find('div', attrs={'id': 'description_inner'})

		if appDesc:			
			self.desc = ''.join(appDesc.findAll(text=True))
			self.desc = self.desc.strip()
			if self.desc == "" or self.desc == None:
				self.desc = "NONE"
		else:
			self.desc = "NONE"

		## Version Search 2 Patterns

		verMatch = verPat.search(html)
		if verMatch:
			self.version = self.GimiVersion(unicode(verMatch.group(1)).encode('utf-8'))
			self.android_version = self.GimiVersion(unicode(verMatch.group(2)).encode('utf-8'))
			if verMatch.group(3):
				self.app2sd = "1"
			else:
				self.app2sd = "0"
		else:
			verMatch1 = varPat1.search(html)
			if verMatch1:
				self.version = self.GimiVersion(unicode(verMatch1.group(1)).encode('utf-8'))
				self.android_version = "0"
				
				if verMatch1.group(2):
					self.app2sd = "1"
				else:
					self.app2sd = "0"
			else:	
				self.version = "0"
				self.android_version = "0"
				self.app2sd = "0"
		
		if self.MetasoftwareVersion != "0":
			self.version = self.MetasoftwareVersion
			
		# Added
		if self.MetadatePublished == "0":
			addedUl = self.soup.find('ul', attrs={'class': 'clList'})
			if addedUl:
				addedLi = addedUl.find('li').contents[1]
				if addedLi:
					lastversiontime = unicode(addedLi.string).encode('utf-8')
					try:
						self.added = time.strptime(lastversiontime,"%b %d, %Y")
						self.added = time.strftime("%Y-%m-%d %H:%M:%S", self.added)
					except ValueError, e:
						try:
							addedLi = addedUl.find('li').contents[2]
							if addedLi:
								lastversiontime = unicode(addedLi.string).encode('utf-8')
								try:
									self.added = time.strptime(lastversiontime,"%b %d, %Y")
									self.added = time.strftime("%Y-%m-%d %H:%M:%S", self.added)
								except ValueError, e:
									try:
										addedLi = addedUl.find('li').contents[3]
										if addedLi:
											lastversiontime = unicode(addedLi.string).encode('utf-8')
											try:
												self.added = time.strptime(lastversiontime,"%b %d, %Y")
												self.added = time.strftime("%Y-%m-%d %H:%M:%S", self.added)
											except ValueError, e:
												self.added = time.strftime('%Y-%m-%d %H:%M:%S')
												
									except ValueError, e:
										self.added = time.strftime('%Y-%m-%d %H:%M:%S')
						except ValueError, e:
							self.added = time.strftime('%Y-%m-%d %H:%M:%S')											
						
			else:
				self.added = time.strftime('%Y-%m-%d %H:%M:%S')
		else:
			self.added = self.MetadatePublished
					
		# Icon
		if self.Metaimage == "0":
			iconMatch = iconPat.search(html)
			if iconMatch: 
				self.icon = unicode(iconMatch.group(1)).encode('utf-8')
			else:
				self.icon = "NONE"
		else:
			self.icon = self.Metaimage

		# Price Free
		
		freematch = freePat.search(html)
		if freematch: 
			self.priceFree = "FREE"
		else:
			self.priceFree = "NONE"
		
		# Price Paid
		paid = self.soup.find('span', attrs={'class': 'pricePaid'})
		if paid: 
			self.pricePaid = unicode(paid.string).encode('utf-8')
		else:
			self.pricePaid = "NONE"
		
		if self.priceFree == "NONE" and self.pricePaid == "NONE":
			self.price = "0"
		elif self.priceFree == "NONE" and self.pricePaid != "NONE":
			self.price = self.GimiFloat(self.pricePaid)
		elif self.pricePaid == "NONE" and self.priceFree != "NONE":
			self.price = "0"
		else:
			self.price = "0"
		
		# Youtube
		youtubeMatch = youtubePat.search(html)
		if youtubeMatch:
			self.youtube = unicode(youtubeMatch.group(1)).encode('utf-8')
		else:
			self.youtube = "0"
		try:
			cursor.execute(r"""SELECT app_id FROM `apps` WHERE `app_hash` = %s LIMIT 1;""",(self.appHash))
			
			if cursor.rowcount == 0:
				try:
					cursor.execute(r"""INSERT IGNORE INTO `android_bulk`.`apps` (`app_id`, `dev_id`, `app_hash`, `app_com`, `app_name`, `app_size`, `app_installs`, `app_rating`, `app_rating_avg`, `app_description`, `app_youtube_id`, `app_version`, `app_App2SD`, `app_os`, `app_os_version`, `app_added`, `app_category`, `app_icon`, `app_price`) VALUES
					(NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",(self.userID, self.appHash, self.ESC(self.comAppName), self.ESC(self.appName), self.ESC(self.size), self.ESC(self.installs), self.ESC(self.votes), self.ESC(self.rating), self.ESC(self.desc), self.ESC(self.youtube), self.ESC(self.version), self.app2sd, '1', self.ESC(self.android_version), self.added, self.categoryID, self.ESC(self.icon), self.ESC(self.price)))

					conn.commit()			
					self.appID = cursor.lastrowid
					appInserted = 1
				except MySQLdb.Warning, e:
					self.printAll()
					sys.exit()
					
				except MySQLdb.Error, e:
					print "Error %d: %s" % (e.args[0], e.args[1])
					return
			else:
				appInserted = 0

		except MySQLdb.Error, e:
			print "Error %d: %s" % (e.args[0], e.args[1])
			return	
		########### APPLICATION INSERT END ########### 
		
		########### IMAGES INSERT START ############## 
		if appDesc:
			images = appDesc.find('div', attrs={'class': 'screenshots'})
			if images:
				a = images.findAll('img')
				s = ""
				for img in a:
					self.screenshots = unicode(img['src']).encode('utf-8')
					if appInserted == 1:
						try:
							cursor.execute(r"""INSERT INTO `android_bulk`.`apps_images` (`id`, `apps_id`, `image_link`) VALUES 
												(NULL, %s, %s);""",(self.appID, self.screenshots))
							conn.commit()						
						except MySQLdb.Error, e:
							print "Error %d: %s" % (e.args[0], e.args[1])
		
		if not self.screenshots:
			self.screenshots = "0"
			
		########### IMAGES INSERT END ############## 

		########### RELATED APPS INSERT ############
		# Related Apps INESRT INTO NEW TABEL
		relatedLis = self.soup.findAll('a', attrs={'class': 'app-item'})
		relatedId = ""
		
		for li in relatedLis:
			relatedLi = unicode(li['href']).encode('utf-8')
			relatedComIdMatch = relatedComIdPat.search(relatedLi)
			if relatedComIdMatch:
				self.related = relatedComIdMatch.group(2)
				self.relatedAppHash = hashlib.md5(relatedComIdMatch.group(2)).hexdigest()
				if appInserted == 1:	
					try:
						cursor.execute(r"""INSERT INTO `android_bulk`.`apps_related` (`related_id`, `app_id`, `related_app_hash`) VALUES 
						(NULL, %s, %s);""",(self.appID, self.relatedAppHash))					
						conn.commit()						
					except MySQLdb.Error, e:
						print "Error  %d: %s" % (e.args[0], e.args[1])
		########### RELATED APPS END ############
	
		# Permissions
		if appInserted == 1:
			self.permissions = self.getPerms(html)
			s = ""
			for p in self.permissions:
				s += unicode(p).encode('utf-8')
			
			if s:
				self.permissions = s
			else:
				self.InsertPerms('0', '0', '0')

		#Market Comments
		if appInserted == 1:		
			for c in self.marketcomments.comments:
				try:		
					c['time'] = time.strptime(c['time'], "%b %d, %Y")
					c['time'] = time.strftime("%Y-%m-%d %H:%M:%S", c['time'])
				except ValueError, e:
					c['time'] = self.usercreated
					
							
				try:
					cursor.execute(r"""INSERT INTO `android_bulk`.`apps_comments` (`apps_comments_id`, `apps_comments_user_id`, `apps_comments_apps_id`, `apps_comments_text`, `apps_comments_added`, `apps_comments_approved`, `apps_comments_ip`, `apps_comment_rating`, `apps_comments_external`) VALUES 
					(NULL, %s, %s, %s, %s, %s, %s, %s, %s);""",('0', self.appID, self.ESC(c['text']), c['time'], '1', '1308875047', c['rating'], self.ESC(c['author'])))
					conn.commit()						
				except MySQLdb.Error, e:
					print "Error %d: %s" % (e.args[0], e.args[1])
					
		if appInserted == 1:
			AndmMrkComMatch = AndmMrkComPath.search(html)
			if AndmMrkComMatch:
				self.AndmMrkCom = unicode(AndmMrkComMatch.group(1)).encode('utf-8')
			
			try:
				cursor.execute(r"""INSERT INTO `android_bulk`.`apps_statistics` (`apps_statistics_id`, `apps_statistic_app_id`, `apps_statistics_comments_total`, `apps_statistics_total_views`, `apps_statistics_total_earned`) VALUES 
				(NULL, %s, %s, %s, %s);""",(self.appID, self.AndmMrkCom, self.votes, '0'))
				conn.commit()						
			except MySQLdb.Error, e:
				print "Error %d: %s" % (e.args[0], e.args[1])
		
		#self.printAll()
		#self.insert()
	def GimiVersion(self, v):
		versionMatch = verNumbPat.search(v)
		if versionMatch:
			return versionMatch.group(1)
		else:
			return "0"
	
	def GimiFloat(self, f):
		floatMatch = floatPat.search(f)
		if floatMatch:
			return floatMatch.group(1)
		else:
			return "0"

	
	def CatchMeta(self):		
		count = 0
		
		self.Metaimage = self.soup.find("meta", attrs={"itemprop":"image"})
		if self.Metaimage:
			self.Metaimage = self.Metaimage['content']
			count += 1
		else:
			self.Metaimage = "0"
			
		self.MetaratingValue = self.soup.find("div", attrs={"class":"ratings rating"})
		if self.MetaratingValue:
			self.MetaratingValue = self.GimiFloat(self.MetaratingValue['content'])
			count += 1
		else:
			self.MetaratingValue = "0"
			
		if self.MetaratingValue == "":
			self.MetaratingValue = "0"
			
		self.Metavotes = self.soup.find("meta", attrs={"class":"votes"})
		if self.Metavotes:
			self.Metavotes = self.GimiVersion(self.Metavotes['content'])
			count += 1
		else:
			self.Metavotes = "0"
			
		if self.Metavotes == "":
			self.Metavotes = "0"
			
		self.MetadatePublished = self.soup.find("meta", attrs={"itemprop":"datePublished"})
		if self.MetadatePublished:
			self.MetadatePublished = self.MetadatePublished['content']
			self.MetadatePublished = time.strptime(self.MetadatePublished, "%Y-%m-%d")
			self.MetadatePublished = time.strftime("%Y-%m-%d %H:%M:%S", self.MetadatePublished)
			count += 1
		else:
			self.MetadatePublished = "0"
			
		if self.MetadatePublished == "":
			self.MetadatePublished = "0"
			
		self.MetasoftwareVersion = self.soup.find("meta", attrs={"itemprop":"softwareVersion"})
		if self.MetasoftwareVersion:
			self.MetasoftwareVersion = self.GimiVersion(self.MetasoftwareVersion['content'])
			count += 1
		else:
			self.MetasoftwareVersion = "0"
			
		if self.MetasoftwareVersion == "":
			self.MetasoftwareVersion = "0"
			
		self.MetaoperatingSystems = self.soup.find("meta", attrs={"itemprop":"operatingSystems"})
		if self.MetaoperatingSystems:
			self.MetaoperatingSystems = self.MetaoperatingSystems['content']
			count += 1
			if self.MetaoperatingSystems == 'Android':
				self.MetaoperatingSystems = '0'
		else:
			self.MetaoperatingSystems = "0"
			
		if self.MetaoperatingSystems == "":
			self.MetaoperatingSystems = "0"
			
		self.MetanumDownloads = self.soup.find("meta", attrs={"itemprop":"numDownloads"})
		if self.MetanumDownloads:
			self.MetanumDownloads = self.MetanumDownloads['content']
			count += 1
		else:
			self.MetanumDownloads = "0"
			
		if self.MetanumDownloads == "":
			self.MetanumDownloads = "0"
			
		self.MetafileSize = self.soup.find("meta", attrs={"itemprop":"fileSize"})
		if self.MetafileSize:
			self.MetafileSize = self.GimiVersion(self.MetafileSize['content'])
			count += 1
		else:
			self.MetafileSize = "0"
			
		if self.MetafileSize == "":
			self.MetafileSize = "0"
			
		if count >= 4:
			try:
				cursor.execute(r"""INSERT IGNORE INTO `android_bulk`.`apps_meta` (`apps_meta_id`, `app_hash`, `apps_meta_image`, `apps_meta_published`, `apps_meta_version`, `apps_meta_os`, `apps_meta_no_download`, `apps_meta_filesize`, `apps_meta_rating`, `apps_meta_votes`) VALUES 
				(NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",(self.appHash, self.Metaimage, self.MetadatePublished, self.MetasoftwareVersion, self.MetaoperatingSystems, self.MetanumDownloads, self.MetafileSize, self.MetaratingValue, self.Metavotes))					
				conn.commit()						
			except MySQLdb.Error, e:
				print "Error  %d: %s" % (e.args[0], e.args[1])
		
		"""
		print "MATA INFO: "
		print 'image: ', self.Metaimage
		print 'datePublished: ', self.MetadatePublished
		print 'softwareVersion: ', self.MetasoftwareVersion
		print 'operatingSystems: ', self.MetaoperatingSystems
		print 'numDownloads: ', self.MetanumDownloads
		print 'fileSize: ', self.MetafileSize
		"""
		
		

	
	def InsertPerms(self, group, perm, type):
		if type == '1':
			# Check if Group Exsist if not insert
			try:
				cursor.execute(r"""SELECT list_perm_id FROM `list_permissions` WHERE `list_perm_name` = %s LIMIT 1;""",(group))
				
				## If Group Not Exsist Insert
				if cursor.rowcount == 0:
					try:
						cursor.execute(r"""INSERT INTO `android_bulk`.`list_permissions` (`list_perm_id`, `list_perm_parent`, `list_perm_name`, `list_perm_description`, `list_perm_operating_system`) VALUES 
				(NULL, %s, %s, %s, %s);""",('0', group, group, '0'))
						conn.commit()
						self.permGroupID = cursor.lastrowid
											
					except MySQLdb.Error, e:
						print "Error  %d: %s" % (e.args[0], e.args[1])
				else:
					self.permGroupID = cursor.fetchone()[0]					
						
			except MySQLdb.Error, e:
				print "Error %d: %s" % (e.args[0], e.args[1])
				
			# Check if Perm Exsist
			try:
				cursor.execute(r"""SELECT list_perm_id FROM `list_permissions` WHERE `list_perm_name` = %s LIMIT 1;""",(perm))
				
				if cursor.rowcount > 0:
					permPermID0 = cursor.fetchone()[0]
				else:
					permPermID0 = "0"
						
				
				## If Perm Not Exsist Insert
				if cursor.rowcount == 0:
					try:
						cursor.execute(r"""INSERT INTO `android_bulk`.`list_permissions` (`list_perm_id`, `list_perm_parent`, `list_perm_name`, `list_perm_description`, `list_perm_operating_system`) VALUES 
				(NULL, %s, %s, %s, %s);""",(self.permGroupID, perm, perm, '0'))
						conn.commit()
						self.permPermID = cursor.lastrowid
											
					except MySQLdb.Error, e:
						print "Error  %d: %s" % (e.args[0], e.args[1])
				else:
					self.permPermID = permPermID0		
								
						
			except MySQLdb.Error, e:
				print "Error %d: %s" % (e.args[0], e.args[1])
				
			# After Group And Perm Insert in App Details
			try:
				#print "Group: ", self.permGroupID
				#print "Perm: ", self.permPermID
				
				cursor.execute(r"""INSERT INTO `android_bulk`.`apps_permissions` (`perm_id`, `apps_id`, `perm_parent`, `perm_child`) VALUES 
				(NULL, %s, %s, %s);""",(self.appID, self.permGroupID, self.permPermID))
				conn.commit()
											
			except MySQLdb.Error, e:
				print "Error  %d: %s" % (e.args[0], e.args[1])			
				
				
	def unquote_u(self, source):
		result = unquote(source)
		if '%u' in result:
			result = result.replace('%u','\\u').decode('unicode_escape')
		if '+' in result:
			result = result.replace('+','').decode('unicode_escape')
			
		return result
    
	def Comments(self, html):
		data = ""		
		data = self.soup.findAll('div', attrs={'class': 'comment'})
		for da in data:
			relatedLi = da.soup.find('div', attrs={'class': 'c_rating'})
			print relatedLi			
		return

	def getPerms(self, text):
		groups = []
		perms = []
		groupInfos = []
		index = 0

		# Find all permission groups and their Names and End_Indexes
		while True:
			pgm = pgp.search(text, index)
			if pgm:
				groupInfos.append( [pgm.group(1), pgm.end()] )
				#print pgm.group(1)
				index = pgm.end()
			else: break
		ln = len(groupInfos)
		for i in xrange(ln):
			if i < ln -1:
				groupInfos[i].append( groupInfos[i+1][1] )		
				
			else:
				groupInfos[i].append( len(text)-1 )
				
			

		# Then look for all permissions for each group
		for g in groupInfos:
			start = g[1]
			end = g[2]
			perms = []
			while True:
				pm = pp.search(text, start, end)
				if pm:
					## GROUP print g[0]
					perms.append( pm.group(1) )					
					## PERM print pm.group(1)
					if g[0] or pm.group(1):
						self.InsertPerms(g[0], pm.group(1), '1')
					start = pm.end()
				else:
					break
			groups.append( (g[0], perms) )
			

		return groups

	def printAll(self):
		print "***********************************************"
		print "COM Name:", self.comAppName
		print "Hash:", self.appHash
		print "App Name:", self.appName		
		print 'Installs: ', self.installs
		print 'Votes: ', self.votes
		print 'Rating: ', self.rating
		print 'Size: ', self.size		
		#print 'Screenshots: ', self.screenshots
		print 'Desc: ', self.desc		
		print 'Version: ', self.version
		print 'Android Version: ', self.android_version
		print 'App2SD: ', self.app2sd		
		print 'Added: ', self.added
		print 'Category: ', self.categ		
		print 'Icon: ', self.icon
		print 'Developer: ', self.developer
		print 'Price Free: ', self.priceFree
		print 'Price Paid: ', self.pricePaid				
		print 'Official Page: ', self.officialPage
		print 'Contact: ', self.contact
		print 'Youtube: ', self.youtube			
		#self.related	
		#print 'Permissions: ', self.permissions
		
	def ESC(self, string):
		string = string.strip()
		string = str(MySQLdb.escape_string(string))
		return string
		
class Comments:
	def __init__(self, soup):
		self.comments = []

		commentTags = soup.findAll('div', attrs={'class': 'comment'})
		goodComments = []
		for c in commentTags:
			if c.has_key('id'):
				goodComments.append(c)

		for c in goodComments:
			self.comments.append(self.parseComment(c))

		#for c in self.comments:
		#	print c

	def parseComment(self, c):
		com = {}

		rDiv = c.find('div', attrs={'class': 'c_rating'})
		if rDiv:
			rVal = rDiv.find('div')['class']
			com['rating'] = unicode(rVal[-1:]).encode('utf-8')
			if com['rating'] == "None":
				com['rating'] = "0"
		else:
			com['rating'] = "0"
			
		if com['rating'] == "":
			com['rating'] = "0"

		aDiv = c.find('div', attrs={'class': 'c_author'})
		if aDiv:
			aSpan = aDiv.find('span', attrs={'class': 'commenter'})
			if aSpan:
				com['author'] = unicode(aSpan.string).encode('utf-8')
				if com['author'] == "None":
					com['author'] = "Unknown"
			else:
				com['author'] = "0"
				
			tSpan = aDiv.find('span', attrs={'class': 'ctime'})
			if tSpan:
				com['time'] = unicode(tSpan.string).encode('utf-8')
				if com['time'] == "None":
					com['time'] = "0"
			else:
				com['time'] = "0"
		
		if com['author'] == "":
			com['author'] = "0"
		
		if com['time'] == "":
			com['time'] = "0"

		textDiv = c.find('div', attrs={'class': 'ctext'})
		if textDiv:
			com['text'] = unicode(textDiv.string).encode('utf-8')
			if com['text'] == "None":
				com['text'] = "NULL"
		else:
			com['text'] = "0"
			
		if com['text'] == "":
			com['text'] = "NULL"

		return com
		
		
if __name__ == '__main__':
	main(sys.argv)
