import os
import zipfile

from selenium import webdriver

PROXY_HOST = '191.102.166.111'  # rotating proxy
PROXY_PORT = 12345
PROXY_USER = 'buddy007'
PROXY_PASS = 'Matt0071!'


manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Firefox Proxy",
    "browser_specific_settings": {
        "gecko": {
	        "id": "addon@example.com",      
	        "strict_min_version": "54.0a1"
        }
    },
    
    "background": {
        "scripts": ["background.js"]
    },

    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ]
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

browser.proxy.settings.set({value: config, scope: "regular"}, function() {});

function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}

browser.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)


def get_chromedriver(use_proxy=False, user_agent=None):
    path = os.path.dirname(os.path.abspath(__file__))
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("detach", True)

    if use_proxy:
        filename=PROXY_HOST.replace('.','_')
        pluginfile = filename+'.xpi'
        print(pluginfile)
        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        chrome_options.add_extension(pluginfile)
    if user_agent:
        chrome_options.add_argument('--user-agent=%s' % user_agent)
    driver = webdriver.Chrome(
        os.path.join(path, 'chromedriver'),
        chrome_options=chrome_options)
    return driver

def main():
    driver = get_chromedriver(use_proxy=True)
    #driver.get('https://www.google.com/search?q=my+ip+address')
    #driver.get('https://httpbin.org/ip')

if __name__ == '__main__':
    main()