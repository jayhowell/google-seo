from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.proxy import Proxy
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from base64 import b64encode


import re
import time

class Browser:
    number_regex = "(:?^|\s)(?=.)((?:0|(?:[1-9](?:\d*|\d{0,2}(?:,\d{3})*)))?(?:\.\d*[1-9])?)(?!\S)"
    
    def __init__(self, headless,browserProxy=None, browsertype="firefox"):
        #TODO: add browser type, proxy and make it headless    
        firefox_capabilities = webdriver.DesiredCapabilities.FIREFOX
        firefox_capabilities['marionette'] = True        
        #define the proxy if someone has set one
        profile = webdriver.FirefoxProfile()
        fireFoxOptions = webdriver.FirefoxOptions()
       
        if browserProxy is not None:         
            #parse browserproxy
            browserProxyTokens = browserProxy.split('@') #split username:pass vs server
            useridpasstokens = browserProxyTokens[0].split(':')
            serverporttokens = browserProxyTokens[1].split(':')
            port = int(serverporttokens[1])
            server = serverporttokens[0]
            proxy_username = useridpasstokens[0]
            proxy_password = useridpasstokens[1]
            profile.set_preference("network.proxy.type", 1) #manual proxy configuration in the browser
            #profile.set_preference("network.proxy.http", server)
            #profile.set_preference("network.proxy.http_port", port)
            profile.set_preference("network.proxy.http", server)
            profile.set_preference("network.proxy.http_port", port)
            profile.set_preference("network.proxy.ssl", server)
            profile.set_preference("network.proxy.ssl_port", port)
            profile.update_preferences()

        fireFoxOptions.set_preference('xpinstall.signatures.required', 0)
        #Make the browser headless, we don't need to see a million browser screens
        if headless:
            fireFoxOptions.set_headless()
        driver = webdriver.Firefox(capabilities=firefox_capabilities,firefox_options=fireFoxOptions,firefox_profile=profile)       
        self.seleniumBrowser=driver

    # Close the browser out, so you don't leak.
    # Note: you don't want to close the browser until you're done with it.
    # Note: becuase constructing a browser is heavy, you want to pool these instances and close them when they are coming out of the pool
    def closeBrowser(self):
        self.seleniumBrowser.close()
    # Gets the number from goggle of all the sites where the keywords are in title
    # except: Exception when the Google doesn't sent back a number.
    # TODO: when we pool the browser instances, we may want to throw away the instance of the browser when we get an excpeiton or we should wait for a while. 
    # If we pause to let the instance recover,if the proxy is bad, we'll continue for ever.  
    def getAllInTitle(self,keywords):
        self.seleniumBrowser.get('https://www.google.com/search?q=allintitle%3A'+keywords)
        try:
            elem = self.seleniumBrowser.find_element_by_id('result-stats')  
            match = re.search(self.number_regex,elem.text)
        except NoSuchElementException:
            raise Exception("Corrupted Call - please wait 5 minutes")
        return int(match.group().replace(",", ''))
    #Gets the number from google of all the sites where the keywords are in the URL
    def getAllInURL(self,keywords):
        self.seleniumBrowser.get('https://www.google.com/search?q=allinurl%3A'+keywords)
        elem = self.seleniumBrowser.find_element_by_id('result-stats')  
        match = re.search(self.number_regex,elem.text)
        return int(match.group().replace(",", ''))
    #just a basic URL get
    def getURL(self, url):
        self.seleniumBrowser.get(url)
        


        
         


