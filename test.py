from selenium import webdriver

 

PROXY_HOST = "179.61.136.249"

PROXY_PORT = 12345

USERNAME = "buddy007" 

PASSWORD = "Matt0071!"

 

profile = webdriver.FirefoxProfile()

profile.set_preference("network.proxy.type", 1)

profile.set_preference("network.proxy.http", PROXY_HOST)

profile.set_preference("network.proxy.http_port", PROXY_PORT)

profile.set_preference("network.proxy.socks_username", USERNAME)

profile.set_preference("network.proxy.socks_password", PASSWORD)

 

profile.update_preferences()

 

# executable_path  = define the path if u don't already have in the PATH system variable. 

browser = webdriver.Firefox(firefox_profile=profile)

browser.get('https://www.intellipaat.com/')

browser.maximize_window()