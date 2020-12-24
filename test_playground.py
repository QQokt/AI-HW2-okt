# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options

# options = Options()
# options.add_argument('--headless')
# options.add_argument('--disable-gpu')
# options.add_argument('--disable-dev-shm-usage')
# options.add_argument('--no-sandbox')
# options.add_argument('blink-settings=imagesEnabled=false') # 不載入圖片
# driver = webdriver.Chrome(options=options)
# driver.get("https://www.maxlist.xyz/2019/04/27/python-selenium-error/")
# driver.set_page_load_timeout(30)
# elems = driver.find_elements_by_xpath("//a[@href]")
# for elem in elems:
#     print(elem.get_attribute("href"))

# driver.get("https://www.gamer.com.tw/")
# elems = driver.find_elements_by_xpath("//a[@href]")
# for elem in elems:
#     print(elem.get_attribute("href"))
ll = 'http://test.com/asasa/wewewwewe?wewew.php'.split('/')
print(ll)
print('/'.join(ll[:len(ll)-1]))
#print(ll[0] +'//' + ll[2])
