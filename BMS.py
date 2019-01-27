import re
import requests

class BookMyShowClient(object):
	NOW_SHOWING_REGEX = '{"event":"productClick","ecommerce":{"currencyCode":"INR","click":{"actionField":{"list":"Filter Impression:category\\\/now showing"},"products":\[{"name":"(.*?)","id":"(.*?)","category":"(.*?)","variant":"(.*?)","position":(.*?),"dimension13":"(.*?)"}\]}}}'
	COMING_SOON_REGEX = '{"event":"productClick","ecommerce":{"currencyCode":"INR","click":{"actionField":{"list":"category\\\/coming soon"},"products":{"name":"(.*?)","id":"(.*?)","category":"(.*?)","variant":"(.*?)","position":(.*?),"dimension13":"(.*?)"}}}}'
	DETAILED_REGEX = '{"VenueCode":"(.*?)","EventCode":"(.*?)","SessionId":(.*?),"ShowTime":"(.*?)","ShowTimeCode":"(.*?)","MinPrice":"(.*?)","MaxPrice":"(.*?)","Availability":"(.*?)","CutOffFlag":"(.*?)","ShowDateTime":"(.*?)","CutOffDateTime":"(.*?)","BestBuy":"(.*?)","ShowDateCode":"(.*?)","IsAtmosEnabled":"(.*?)","SessionUnpaidFlag":"(.*?)","SessionUnpaidQuota":"(.*?)","BestAvailableSeats":(.*?),"Attributes":"(.*?)","SessionCodFlag":"(.*?)","SessionCodQuota":"(.*?)","SessionCopFlag":"(.*?)","SessionCopQuota":"(.*?)","SessionPopUpDesc":"(.*?)","Class":"(.*?)"}'
	VENUE_REGEX = '{"VenueCode":"(.*?)","VenueName":"(.*?)","VenueAdd":"(.*?)","VenueLegends":"(.*?)","VenueOffers":"(.*?)","SessCount":"(.*?)","AllowSales":"(.*?)","CompCode":"(.*?)","Lat":"(.*?)","Lng":"(.*?)","SubRegCode":"(.*?)","SubRegName":"(.*?)","SubRegSeq":"(.*?)","VenueApp":"(.*?)","IsNewCinema":"(.*?)","IsFoodSales":"(.*?)","IsMultiplex":"(.*?)","IsFullSeatLayout":"(.*?)","Message":"(.*?)","MessageType":"(.*?)","MessageTitle":"(.*?)","CinemaUnpaidFlag":"(.*?)","MTicket":"(.*?)","PopUpDescription":"(.*?)","IsFullLayout":"(.*?)","CinemaCodFlag":"(.*?)","CinemaCopFlag":"(.*?)","TicketCancellation":"(.*?)","VenueInfoMessage":"(.*?)"}'
	

	def __init__(self, location):
		self.__location = location.lower()
		self.__url = "https://in.bookmyshow.com/%s/movies" % self.__location
		self.__html = None

	def set_url(self, url):
		self.__url = url
		self.__html = None

	def __download(self):
		req = requests.get(self.__url, headers={'User-Agent' : "Magic Browser"})
		html = req.text
		# print req.url
		return html.encode('ascii', 'ignore').decode('utf-8')

	def compare(self, left, right, movie_name, text) : 
		i = left
		j = 0
		while i < right and j < len(movie_name): 
			if not movie_name[j].isalnum() : 
				j += 1
			if not text[i].isalnum() : 
				i += 1
			if (j < len(movie_name) and i < right) and (movie_name[j].isalnum() and text[i].isalnum()) : 
				if movie_name[j].lower() != text[i].lower() : 
					return False
				else : 
					i += 1
					j += 1

		return True

	def get_now_showing(self):
		if not self.__html:
			self.__html = self.__download()
		now_showing = re.findall(self.NOW_SHOWING_REGEX, self.__html)

		"""
		This is done to add the buy URL to now_showing tuple 
		"""
		found = set()
		for index in re.finditer("/buytickets/", self.__html) : 
			left = index.start() 
			right = self.__html.find(self.__location, left + 1)
			# print left, right
			name = self.__html[left:right]
			
			if name not in found : 
				# print left, right, name
				found.add(name)
				for i in range(0, len(now_showing)) : 
					if self.compare(left + len("/buytickets/"), right, now_showing[i][0], self.__html): 
						# print "URL::", self.__html[left:self.__html.find("\"", left + 1)]
						# Url added here
						now_showing[i] += ("https://in.bookmyshow.com" + self.__html[left:self.__html.find("\"", left + 1)], ) 
						break

		found.clear()

		image_urls = re.findall("data-src=\"(.*?)\"", self.__html)
		for url in image_urls : 
			left = url.find("/large/") + len("/large/")
			right = len(url) - 35 # 35 characters at the end do not contribute to the name of the movie
			name = url[left : right]
			# print name, url, "\n"

			if name not in found : 
				found.add(name)
				for i in range(0, len(now_showing)) : 
					if self.compare(left, right, now_showing[i][0], url) :
						now_showing[i] += ("https:" + url, )
						break

		return now_showing

	def get_coming_soon(self):
		if not self.__html:
			self.__html = self.__download()
		coming_soon = re.findall(self.COMING_SOON_REGEX, self.__html)
		return coming_soon

	def get_details(self):
		if not self.__html:
			self.__html = self.__download()
			
		venue = re.findall(self.VENUE_REGEX, self.__html)
		venue_list = dict()
		for row in venue:
			venue_list[row[0]] = row[1]		# row[0] is venue code and row[1] is the venue name



		details = re.findall(self.DETAILED_REGEX, self.__html).decode('utf-8')
		show_list = []
		for row in details:
			current = {}
			current['theatre_name'] = venue_list[row[0]]    # add theatre name
			current['show_time'] = row[3]                   # add time
			current['time_code'] = row[4]                   # add time code for eg '1700'
			current['min_price'] = row[5]					# For eg : '60.00'
			current['max_price'] = row[6]					# For eg : '70.00'
			current['class'] = row[-1]                      # Morning, afternoon
			show_list.append(current)
		return show_list



if __name__ ==  "__main__":
	bms = BookMyShowClient("pune")
	print("Get Now Showing")
	print(bms.get_now_showing())


