from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.binary_location = '/usr/local/bin/chromedriver'
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')

options.add_argument('--no-sandbox')
options.add_argument('blink-settings=imagesEnabled=false') #不加载图片, 提升速度


driver = webdriver.Chrome(options=options)


# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys


# driver = webdriver.Chrome()
# driver.get("https://www.gamer.com.tw/")

# elems = driver.find_elements_by_xpath("//a[@href]")
# for elem in elems:
#     print(elem.get_attribute("href"))