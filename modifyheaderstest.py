import time  
import re  
from base64 import b64encode  
from selenium import webdriver  
  
# http://www.garethhunt.com/modifyheaders/help/?v=0.7.1.1  
MODIFY_HEADERS_EXTENSION = 'modify_header_value_http_headers-0.1.7-an+fx.xpi'  
  
def get_firefox(proxy):  
    fp = webdriver.FirefoxProfile()  
    m = re.compile('([^:]+):([^\@]+)\@([\d\.]+):(\d+)').search(proxy)    
    if m:  
        #print 'Set proxy into {}'.format(proxy)  
        # Extract parameters of agent   
        proxy_username = m.groups()[0]    
        proxy_password = m.groups()[1]    
        proxy_host = m.groups()[2]    
        proxy_port = int(m.groups()[3])  
        # Set proxy parameters  
        fp.set_preference('network.proxy.type', 1)  
        fp.set_preference('network.proxy.http', proxy_host)  
        fp.set_preference('network.proxy.http_port', proxy_port)  
        fp.set_preference('network.proxy.ssl', proxy_host)  
        fp.set_preference('network.proxy.ssl_port', proxy_port)  
        credentials = '{}:{}'.format(proxy_username, proxy_password)  
        cred_byptes = credentials.encode()
        credentials = b64encode(cred_byptes)  
        # add Modify Headers  
        fp.add_extension(MODIFY_HEADERS_EXTENSION)  
        fp.set_preference('modifyheaders.config.active', True)  
        fp.set_preference('modifyheaders.headers.count', 1)  
        # add Proxy-Authorization head
        fp.set_preference('modifyheaders.headers.action0', 'Add')  
        fp.set_preference('modifyheaders.headers.name0', 'Proxy-Authorization')  
        fp.set_preference("modifyheaders.headers.value0", 'Basic {}'.format(credentials))  
        fp.set_preference('modifyheaders.headers.enabled0', True)                       
    firefox = webdriver.Firefox(firefox_profile=fp)  
    return firefox  
  
def test():  
    firefox = get_firefox(proxy='buddy007:Matt0071!@191.102.166.111:12345')  
    # visit http://httpbin.org/ip  get current ip address
    firefox.get('https://httpbin.org/ip')  
    time.sleep(1000)  
      
if __name__ == '__main__':  
    test()