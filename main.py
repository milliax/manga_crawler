from selenium import webdriver
import time
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
import json

from browsermobproxy import Server


if __name__ == "__main__":

    number = input("請輸入番號：")
    book = input("請輸入書號：")


    """ start up proxy server to collect data """
    server = Server("./browsermob-proxy/bin/browsermob-proxy")
    server.start()
    proxy = server.create_proxy({'captureHeaders': True, 'captureContent': True, 'captureBinaryContent': True})

    """ adding chrome options """
    #service_args = ["--proxy=%s" % proxy.proxy, '--ignore-ssl-errors=yes']
    chrome_options = Options()
    chrome_options.add_argument("--proxy-server={0}".format(proxy.proxy))
    chrome_options.add_argument("ignore-certificate-errors")

    """ Open controlable google chrome """
    driver = webdriver.Chrome("./chromedriver",options=chrome_options)

    """ Open URL """
    driver.get(
        "https://www.cartoonmad.com/comic/{number}.html".format(number=number))

    """ Entering target URL """
    button = driver.find_element_by_link_text("第 {book} 卷".format(book=book))
    proxy.new_har() # start recording
    button.click()

    """ wait for the requests """
    time.sleep(5)
    print(proxy)