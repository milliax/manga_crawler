from selenium import webdriver
import time
from selenium.webdriver.chrome.options import Options
from browsermobproxy import Server
from bs4 import BeautifulSoup
import re
import requests
from fpdf import FPDF
import multiprocessing
import os

header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"}


def format_number(value):
    value_in_string = str(value)
    if len(value_in_string) == 1:
        return "00"+value_in_string
    elif len(value_in_string) == 2:
        return "0"+value_in_string
    else:
        return value_in_string


def chdir(ds):
    dlist = ds.split(os.path.sep)
    for d in dlist:
        if not os.path.exists(d) and not os.path.isdir(d):
            os.mkdir(d)
        os.chdir(d)


crawl_list = []

def main():

    """ book series url input """
    while True:
        print('輸入作品目錄URL:', end='')
        url = input()
        try:
            if re.match(r'https://www\.cartoonmad\.com/comic/[0-9]+\.html', url).group(0):
                break
        except:
            print('無效的網址')
            continue

    res = requests.get(url)
    res.encoding = "big5"
    bs = BeautifulSoup(res.text, 'html.parser')
    chs = bs.select('#info a[href^="/comic/"]')
    bname = bs.select(
        'td[style="font-size:12pt;color:#000066"] a[href^="/comic/"]')[0].text
    chdir(bname)
    print('標題: %s' % bname)

    """ book numbers input """
    
    print('請選擇下載話數(ex:1-2 5-8 10 將會下載編號1, 2, 5, 6, 7, 8, 10的章節)')
    choose_chs = input()
    tmp = re.findall(r'[0-9]+\-?[0-9]*', choose_chs)
    choose_block_list = []
    for block in tmp:
        try:
            block = block.split('-')
            for i in range(len(block)):
                block[i] = int(block[i])
                if block[i] < 0:
                    raise Exception('out of range')
            if len(block) >= 2:
                if block[1] < block[0]:
                    block[0], block[1] = block[1], block[0]
                choose_block_list.append([block[0], block[1]])
            else:
                choose_block_list.append([block[0], block[0]])
        except:
            continue

    print(choose_block_list)
    books_to_crawl = []
    for e in choose_block_list:
        books_to_crawl.append([x for x in range(e[0],e[1]+1)])
    books_to_crawl = [item for sublist in books_to_crawl for item in sublist]
    print(books_to_crawl)
    return

    """ start up proxy server to collect data """
    server = Server("./browsermob-proxy/bin/browsermob-proxy")
    server.start()
    proxy = server.create_proxy(
        {'captureHeaders': True, 'captureContent': True, 'captureBinaryContent': True})

    """ adding chrome options """
    #service_args = ["--proxy=%s" % proxy.proxy, '--ignore-ssl-errors=yes']
    chrome_options = Options()
    chrome_options.add_argument("--proxy-server={0}".format(proxy.proxy))
    chrome_options.add_argument("ignore-certificate-errors")

    """ Open controlable google chrome """
    driver = webdriver.Chrome("./chromedriver", options=chrome_options)

    """ Open URL """
    driver.get(url)

    """ Entering target URL """
    button = driver.find_element_by_link_text("第 001 卷")
    # start recording
    time.sleep(1)
    proxy.new_har("new_har", options={'captureContent': True})
    button.click()

    """ wait for the requests """
    time.sleep(5)
    result = proxy.har
    count = 20

    press_link = False
    link = ""

    queue = []

    for entry in result["log"]["entries"]:
        # print(entry["response"]["content"])
        pack = entry["response"]["content"]

        if(pack["mimeType"] != "text/html"):
            continue

        redirect_Message = "<head><title>Object moved</title></head>"
        if(pack["text"][:39] == redirect_Message[:39]):
            # print(pack)
            press_link = True

            datum = BeautifulSoup(pack["text"], "html.parser")
            queue.append(datum.find_all("a")[0]["href"])

    driver.quit()  # close all tabs

    root = queue[2]
    print(root)

    book_rid = root.split("/")[3]
    book_id = root.split("/")[4]

    manga_book = {}
    pages = 1
    while True:
        try:
            image_data = requests.get("https://www.cartoonmad.com/{0}/{1}/{2}/{3}.jpg".format(
                book_rid, book_id, format_number(book), format_number(pages)), headers=header)

            print("\rget: {}".format(pages), end="")

            if image_data.ok:
                manga_book.append(image_data.content)
            else:
                break
        except:
            break

    pdf_path = "./{0}.pdf".format(book)

    pdf = FPDF()
    for manga_page in manga_book:
        pdf.add_page()
        pdf.image(manga_page)
    pdf.output(pdf_path, "F")


if __name__ == "__main__":
    main()