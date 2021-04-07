from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from pyresourcepool.pyresourcepool import ResourcePool
from threading import Thread
import os
import zipfile
import re
import time

manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
"""

background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
          singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
          },
          bypassList: ["localhost"]
        }
      };

chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}

chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
"""

# Move to base Browser class
# Object to encapsulate the proxy information
class Proxy:
    host=None
    port=None
    username=None
    password=None
    def __init__(self, proxystring):
        p = '((?P<name>.+):(?P<password>.+)@)?(?P<host>.+):(?P<port>.+)'   
        match = re.search(p,proxystring)
        self.host = match.group('host')
        self.port = match.group('port')
        self.username = match.group('name')
        self.password = match.group('password')

class ChromeBrowser:
    number_regex = "(:?^|\s)(?=.)((?:0|(?:[1-9](?:\d*|\d{0,2}(?:,\d{3})*)))?(?:\.\d*[1-9])?)(?!\S)"
    #The delay and failed attempts really should be in a separate class called pooledObject
    #TODO: make this better by extracting pooled logic into a seprate class that contains browser.
    #number of failed attempts.
    failed = False
    failedAttempts =0
    proxy=None
    pluginfile=None
    poolReturnTime=120
    
    def __init__(self, headless=True,browserProxy=None, browsertype="chrome"):
                       
        if browserProxy:
            self.proxy = Proxy(browserProxy)
            self.createBrowserProxyPlugin()
            
        self.seleniumBrowser=self.openBrowser(headless)

    def __del__(self): 
        self.printLog("closing browser")
        self.closeBrowser() 

    def createBrowserProxyPlugin(self):
        newbackground_js = background_js % (self.proxy.host, self.proxy.port, self.proxy.username, self.proxy.password)
        self.pluginfile=self.proxy.host.replace('.','_')+".zip"
        with zipfile.ZipFile(self.pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", newbackground_js)
        print(self.pluginfile)

    def printLog(self, logString):
        logString = "[{}] "+ str(logString)
        print(logString.format(self.proxy.host))
    # Close the browser out, so you don't leak.
    # Note: you don't want to close the browser until you're done with it.
    # Note: becuase constructing a browser is heavy, you want to pool these instances and close them when they are coming out of the pool
    def closeBrowser(self):
        self.seleniumBrowser.close()
    # Gets the number from goggle for both all in url and all in title.
    
    def openBrowser(self, headless=True):
        #TODO: add browser type, proxy and make it headless    
        chrome_capabilities = webdriver.DesiredCapabilities.CHROME
        chrome_capabilities['marionette'] = True  
        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.add_argument("--incognito")
        #added detatch so I can see the page the browser opens. Take this out when we start moving into production
        chromeOptions.add_experimental_option("detach", True)
        #Make the browser headless, we don't need to see a million browser screens
        #fireFoxOptions.add_argument("--user-data-dir=/home/jhowell/selfirefox")
        if(self.pluginfile is not None):
            chromeOptions.add_extension(self.pluginfile)

        #if headless:
        #    chromeOptions.set_headless()
        driver = webdriver.Chrome(desired_capabilities=chrome_capabilities,chrome_options=chromeOptions)
        return driver

    def isValid(self):
        ipaddress = self.getExternalIpAddress()
        if self.proxy.host == ipaddress:
            self.printLog("proxy:"+ipaddress+"is valid")
            return True
        else:
            return False

    
    #####################################################################
    # TODO: when we pool the browser instances, we may want to throw away the instance of the browser when we get an excpeiton or we should wait for a while. 
    # If we pause to let the instance recover,if the proxy is bad, we'll continue for ever.  
    # x is either 'title' or 'url', with a default of title
    #####################################################################
    def getAllInx(self,keywords,x='title'):
        numberstring = self.getTextfromURL('https://www.google.com/search?q=allin'+x+'%3A'+keywords,self.number_regex,'result-stats')
        #self.failed=True #testing this functionality.
        return int(numberstring.replace(",", ''))
   
    def getURL(self, url):
        self.seleniumBrowser.get(url)  

    #used to see if we have a good proxy
    def getExternalIpAddress(self):  
        externalIpString = self.getTextfromURL('https://whatismyipaddress.com/','[0-9]+(?:\.[0-9]+){3}','ipv4')
        return externalIpString
       

    ########################################################################    
    # priave function so that we can put all of our excepiton tracking logic in one place when we go and try to get things from the html page.
    # Arguments
    #       requestURL - the url being requested
    #       regex - regular expression used to parse the element resulting in a string
    #       elem_name - the name of the element to be searched in the page
    #       elem_type - the type of element used to search the page. currently only id and classname are used to search the webpage.
    # Exceptions raised
    #       Proxy error exception - when the proxy fails and is not available and or proxy credentials aren't right.
    #       Google timeout error - when google prompts us witha robot picture becuase it's been too soon since we last asked
    #       Google no results returned - when google for whatever reason will not return any results
    ########################################################################
    def getTextfromURL(self,requestURL,regex,elem_name,elem_type='id'):
        self.seleniumBrowser.get(requestURL)
        try:
            if elem_type is 'id':
                elem = self.seleniumBrowser.find_element_by_id(elem_name)  
            else:
                elem = self.seleniumBrowser.find_element_by_class_name(elem_name)
            match = re.search(regex,elem.text)
            if match is None:
                raise NoSuchElementException("regex "+ regex + " found for "+requestURL) 
            return match.group() 
        except NoSuchElementException as exception: #we didn't get the element back we expected
            #it is possible that there were no documents matched, so we return 0.
            page_source = self.seleniumBrowser.page_source
            
            googleRobotMatch = re.search("unusual traffic",page_source) #TODO add robot text here.
            if googleRobotMatch: #this is the primary offender that happens the most
                self.printLog("Google Robot page match")
                self.failed=True
                raise exception #TODO replace with google robot exception
            
            noDocumentsMatch = re.search("did not match any documents",page_source)
            if noDocumentsMatch: #if we find the string return o
                self.printLog("Returning 0 - no documents found. URL: "+requestURL)
                return "0"

            noSearchNumbers = re.search("Related searches",page_source)
            if noDocumentsMatch: #if we find the string return o
                self.printLog("Returning 0 - no documents found. URL: "+requestURL)
                return "-1"

            
            # if we get this far, we have no idea why this failed, raise the exception
            self.failed=True 
            raise exception
            
        


# convenience class in case I need to override any of the methods in the pool.  
# right now I should be able to put all pool logic into the return to pool
class BrowserPool(ResourcePool):   
    #add the min and max number of elements
    minInstances=0
    maxInstances=10
    #browserProxy='buddy007:Matt0071!@191.96.253.98:12345'
    proxyIndex=0
    def __init__(self, minInstances=1, maxInstances=10,pooltype="chrome",proxyArray=None):
        #super().__init__(self, [], return_callback=self.poolreturnCallback)
        super().__init__([], return_callback=self.poolreturnCallback)
        self.minInstances = minInstances
        self.maxInstances = maxInstances
        self.proxyArray=proxyArray
        self.addtoMaxInstances()
        #need to keep the index of teh proxy array around so we can continue adding instnaces to the pool, if our proxies start to not work.
        self.proxyIndex=0

    def addtoMaxInstances(self):
        for instances in range(self.maxInstances - super().active_size):
            thread = Thread(target = self.precreateBrowserInstanceCallback)
            thread.start()
            thread.join()
            print("Precreate thread finished")
    
    def precreateBrowserInstanceCallback(self):
        try:                
            self.proxyIndex += 1
            if self.proxyIndex >= len(self.proxyArray):
                self.proxyIndex = 0
                print("exhausted our list of proxies starting over")
            proxyString = self.proxyArray[self.proxyIndex]
            browser = ChromeBrowser(headless=True,browserProxy=proxyString)                
            #if browser.isValid(): #not a valid proxy not adding it
            browser.printLog("Adding new browser")
            self.add(browser)                 
        except WebDriverException as webdriverexception:
            print("Threw an exception Creating selenium instance for proxy "+proxyString+ " : "+str(webdriverexception)) 
        
    def poolreturnCallback(self,browser):
        
        if browser.failed:
            #set the browser fail back to false
            browser.failed=False
            #increment the failed counter
            browser.failedAttempts += 1
            self.precreateBrowserInstanceCallback() #create a new instance
            
            browser.printLog("Removing this brower instance from pool and shuting it down")
            #we have to manually close the browser in the Browswer object, becuase the pool keeps the old objects around

            browser.closeBrowser()
            self.remove(browser) #remove the old instance
            time.sleep(browser.poolReturnTime)
        else: # our browser didn't fail, clear out the variables
            #make sure we reset failure criteria in the browser.
            browser.failed=False
            browser.failedAttempts=0
            
    def get_resource(self):
        #print("getting resource")
        returnob =  super().get_resource()
        return returnob


#pool = BrowserPool(maxInstances=1)
#with pool.get_resource() as browser:
    #print(browser.getExternalIpAddress())
#    if browser.isValid():
#        print(browser.getAllInx("gun sales luger"))
#print("moving on")
#with pool.get_resource() as browser:
#    print(browser.getAllInx("gun sight"))
