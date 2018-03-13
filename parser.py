import urllib2
import feedparser
from bs4 import BeautifulSoup
import sqlite3 as sqlite
import re
import os

from ParseTotxt import ParseTotxt
from ParseTodb import ParseTodb

class Parser:
    def __init__(self,out="txt",rssFile="rssList.txt",quickCheck=False):
        # Set up the output
        if out == "txt":
            self.out = ParseTotxt()
        elif out == "db":
            self.out = ParseTodb()
            
        if quickCheck:
            print 'Warning: This will only be parsing one RSS feed for testing purposes'
            self.rssList={"NYT":"http://www.nytimes.com/services/xml/rss/nyt/HomePage.xml"}
        else:
            # Pulling the data from the rss file
            self.rssList = {} 
            print "Pulling the RSS Feeds list from " + rssFile
            self.setFeedList(rssFile)

    def setFeedList(self,filename):
       file = open(filename)
       for line in file: #? for line in file
            rssName, rssFeed = line.strip().split(' ')
            self.rssList[rssName] = rssFeed
       file.close()

    def parse(self):
        for rssName in self.rssList.keys():
            rssFeed = self.rssList[rssName]
            rss = feedparser.parse(rssFeed)
            print "Connecting to "+rssName
            print "--------------"
            for entry in rss.entries:
                title = entry["title"]
                try:
                    author = entry["author"]
                except:
                    author = "None"
                try:
                    published = str(entry["published_parsed"])
                except:
                    published = "None"
                url = entry["link"]
                try:
                    c = urllib2.urlopen(url)
                except:
                    print "Could not open %s" % url
                    continue
                soup = BeautifulSoup(c.read(),"html.parser")
                self.addtoindex(url, soup, title, rssName, author, published)
        self.out.commit()

    # Index an individual page
    def addtoindex(self, url, soup, title, source, author, published):
            if self.out.isindexed(url): return
            print 'Indexing ' + url
            # Get the individual words
            if source[:2] == "NYT":
                text = self.getArticleNYT(soup)
            else:
                text = self.getArticleP(soup)
            text = text.encode('utf-8') #probleme d'encodage rencontre
            words = self.separatewords(text)
            self.out.add(title, source, author, url, published, words)
        

# Extract the text from an HTML page (no tags)
    def getArticleNYT(self, soup):
        matches = soup.findAll("p", {"class": "story-body-text story-content"})
        resultText = ''
        for p in matches:
            text = self.getText(p)
            resultText += text + '\n'
        return resultText

    def getArticleP(self,soup):
        matches = soup.findAll("p")
        resultText = ''
        for p in matches:
            text = self.getText(p)
            resultText += text + '\n'
        return resultText

    def getText(self,soup):
        v = soup.string
        if v == None:
            c = soup.contents
            resulttext = ''
            for t in c:
                subtext = self.getText(t)
                resulttext += subtext + ' '
            return resulttext
        else:
            return v.strip()

# Separate the words by any non-whitespace character
    def separatewords(self,text):
        splitter = re.compile(r'\W*')
        return self.filter([s.lower() for s in splitter.split(text) if s != ''])

    def filter(self,words):
        return [word for word in words if (len(word)>1 and word.isalpha())] #list comprehension

    def readfile(self):
        return self.out.readfile()