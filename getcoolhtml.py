import chromeBrowser as browser
browserProxy='buddy007:Matt0071!@179.61.136.249:12345'
browser = browser.ChromeBrowser(headless=True,browserProxy=browserProxy)
print("created browser")
try:
    #print(browser.getAllInTitle("gun sight"))
    #print(browser.getAllInURL("gun sight"))
    #browser.getURL("http://www.google.com")
    print(browser.getAllInx("gun sight"))
    print(browser.getAllInx("gun sight",x='url'))

    #print(browser.getExternalIpAddress())
except Exception as exception:
    print(exception)
#browser.closeBrowser()


