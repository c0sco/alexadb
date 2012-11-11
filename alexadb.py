#!/usr/bin/env python

import sys
import urllib2
import re
from xml.sax import saxutils
import json
import pickle

# How many categories deep to go? (e.g. 2 would go Category/Subcategory, 3 is Cat/Subcat/Subcat)
maxDepth = 2

# How long to wait for a URL to load before giving up? (this won't exit the script, just assume the page is an empty string and move on)
siteTimeout = 30

# Global dicts for the data we are saving
allCats = {}
allSites = {}


def main():
	if len(sys.argv) != 2 or sys.argv[1] not in ['python', 'json']:
		print "Need a file format (python or json) to return!"
		exit()

	# Get the main categories page and find all of the categories in the html
	data = getUrlContent('http://www.alexa.com/topsites/category')
	topCats = re.findall(r'href="/topsites/category/Top/(.*?)"', data, re.IGNORECASE)

	# Loop through all the categories
	for aCat in topCats:
		allCats[aCat] = {}
		processCat(aCat, allCats[aCat])

	# Write out the data in the format specified
	if sys.argv[1] == 'json':
		f = open('./allCats.json', 'w')
		f.write(json.dumps(allCats))
		f.close()
		f = open('./allSites.json', 'w')
		f.write(json.dumps(allSites))
		f.close()
	else:
		f = open('./allCats.pickle', 'w')
		pickle.dump(allCats, f)
		f.close()
		f = open('./allSites.pickle', 'w')
		pickle.dump(allSites, f)
		f.close()

	return


def processCat(aCat, catDict):
	# Too deep!
	if len(aCat.split('/')) > maxDepth:
		return

	# Get the main page for this category
	print 'Processing', aCat
	catUrl = 'http://www.alexa.com/topsites/category/Top/' + aCat

	# Get all the sites in this specific category
	getAllSitesForCat(catUrl, catDict, aCat)
	print 'Got all sites'

	# Get all the sub-categories
	catHtml = getUrlContent(catUrl)
	catCats = re.findall(r'href="/topsites/category/Top/' + aCat + r'/(.*?)"', catHtml, re.IGNORECASE)

	# Loop through and process them
	if catCats != None and catCats != []:
		for catCat in catCats:
			catDict[catCat] = {}
			processCat(aCat + '/' + catCat, catDict[catCat])

	return


# Given a category URL, get all the sites (paginated) for it and store them in our global dicts
def getAllSitesForCat(catUrl, catDict, aCat):
	for x in range(20): # Max of 20 pages
		if x == 0:
			# The first page has no pagination number associated
			myUrl = catUrl
		else:
			# All others are in the format of category;<page num>/Category
			myUrl = catUrl.replace('category/', 'category;%d'%x + '/')

		print 'Working on', myUrl
		catHtml = getUrlContent(myUrl)

		if catHtml.find('No sites for this category') > -1:
			break

		# Grab the site rank number, the site name, and the URL
		curCatSites = re.findall(r'class="count">(\d+)</div>.*?<a href=".*?">(.*?)</a>.*?topsites-label">(.*?)</span', 
			catHtml, re.IGNORECASE | re.DOTALL)

		# Loop through our findall results and save the info into our dicts
		for curSite in curCatSites:
			if not allSites.has_key(curSite[2]):
				allSites[curSite[2]] = []

			# Store the category:rank under the url key
			allSites[curSite[2]].append(aCat + ':' + curSite[0])

			# Store the (rank,name,url) tuple under the url key
			catDict[curSite[2]] = curSite

	return


# Open a url and return its contents
def getUrlContent(url):
	url = saxutils.unescape(url)
	try:
		return urllib2.urlopen(url, None, siteTimeout).read()
	except:
		print "Could not get contents of", url
		return ""


if __name__ == "__main__":
	main()
