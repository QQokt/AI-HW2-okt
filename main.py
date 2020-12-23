import re
import os
import sys
import glob
import jpype
import subprocess
import pandas as pd
import xlrd
from bs4 import BeautifulSoup
from subprocess import Popen, PIPE, STDOUT
from datetime import datetime
from http import HTTPStatus
import validators
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
'''
Naive BFS recursion version v001 
'''

''' 全域變數 '''
# Java環境、jar檔路徑
jvm_path = jpype.getDefaultJVMPath()
jar_path = '0.0.2/event.source.page.discovery-0.0.2.jar'

# Test Version
now = datetime.now()
date_time = now.strftime("%Y_%m_%d_%H%M%S")
test_version = 'team4-bfsv000' + date_time

# Selenium 初始化
options = Options()
# options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_argument('blink-settings=imagesEnabled=false')  # 不載入圖片
selenium_driver = webdriver.Chrome(options=options)
selenium_driver.set_page_load_timeout(30)


def get_http_domin_helper(url):
    # url_List = ['https:', '', 'www.ncu.edu.tw', 'events', 'showevent', 'eventid', '9380']
    url_List = url.split('/')
    dname = url_List[0] + '//' + url_List[1] + url_List[2]
    return dname


def get_domin_helper(url):
    url_List = url.split('/')    # url_List = ['http:', '', 'foo.com']
    return url_List[1] + url_List[2]


def filter_file(str):
    """filter_file 過濾網址，判斷一般網址與檔案網址，如果是檔案網址則回傳一個 'x' """
    #     Example Cases:
    # 1. **http://foo.com**
    # 2. **http://foo.com/**
    # 3. **http://foo.com/index.php?page=5**
    # 4. **http://foo.com/file_name.pdf** **NO!**
    # 5. **http://foo.com/index.php**
    # 6. **http://foo.com/bar**
    # 7. **http://foo.com/?bar=5**

    # Case 2, 6 刪除最後一個 '/''
    # ex:http://foo.com/ --> http://foo.com
    if(str[len(str)-1] == '/'):
        str = str[:len(str)-1]

    # Case 3, 4, 5 得到檔名
    # 如果沒有檔名則為 case 1
    # ex:http://foo.com/index.php?page=5 --> ['index.php']
    str1 = re.findall(r'(?<=\/)[^\/\?#]+(?=[^\/]*$)', str)

    # Case 7
    # 回傳原網址:http://foo.com/?bar=5
    if(len(str1) == 0):
        return str

    str1 = str1[0]
    # case 6
    # 回傳原網址:http://foo.com/bar
    if '.' not in str1:
        return str

    # case 1
    if(str1 == get_domin_helper(str)):
        return str
    # case 3, 4, 5
    else:
        file_type = str1.split('.')[1]

        # 正面表列可以搜尋的網頁檔名
        if file_type == 'html' or file_type == 'php' or file_type == 'asp' or file_type == 'aspx' or file_type == 'jsp':
            return str
        else:
            return 'x'


class RequestStatus:
    Unfininsh, Finish, Fail = range(3)


class Search(object):
    '''
    QQ
    '''

    '''統計找到正確答案的數量'''
    trueCount = 0

    def __init__(self, id, URL):
        self.seed_ID = id
        self.seed_URL = URL
        self.isFound = RequestStatus.Unfininsh
        self.BFS_queue = []
        self.cost = 0
        self.max_step = 300
        self.have_visit = set()

        self.ExtractLinks(self.seed_URL)
        self.NavieBFS(self.seed_URL)

    def SearchCallAPI(self, url):
        '''
        根據 id 與 url 去 java 看對不對
        '''
        print('ID : {id} , cost = {cost} {url}'.format(
            id=str(self.seed_ID), cost=self.cost, url=url))
        self.cost += 1

        command = []
        command.append('java')
        command.append('-cp')
        command.append(jar_path)
        command.append(
            'nculab.widm.event.source.page.discovery.QueryEventSourcePage')
        command.append('--test-version')
        command.append(test_version)
        command.append('--url-id')
        command.append(str(self.seed_ID))
        command.append('--query-url')
        command.append(url)
        command.append('--anchor-text')
        command.append('qq')

        with Popen(command, stdout=PIPE, stderr=PIPE) as p:
            output, errors = p.communicate()

        ans = output.decode('utf-8').splitlines()[0]

        print(ans)

        if 'true' in ans:
            self.trueCount = self.trueCount + 1
            self.isFound = RequestStatus.Finish

    def NavieBFS(self, URL):
        while(self.isFound == RequestStatus.Unfininsh):
            if(self.cost > self.max_step):
                self.isFound = RequestStatus.Fail
                break
            if(len(self.BFS_queue) == 0):
                self.isFound = RequestStatus.Fail
                break

            # 確認網址型式正確
            if validators.url(self.BFS_queue[0]) != True:
                if self.BFS_queue[0] == self.seed_URL:
                    self.isFound = RequestStatus.Fail
                    return
                self.BFS_queue.pop(0)
                continue
            self.ExtractLinks(self.BFS_queue[0])
            self.BFS_queue.pop(0)

    def ExtractLinks(self, url):
        '''
        ExtractLinks
        根據輸入的 URL 搜尋該網頁原始碼中的連結
        '''
        extract_queue = []

        # 將該網頁之下的原始碼取出，且設定請求的 timeout，如果超過就放棄
        try:
            selenium_driver.get(url)
        except:
            print('Error')
            if url == self.seed_URL:
                self.isFound = RequestStatus.Fail
            return

        try:
            elems = selenium_driver.find_elements_by_xpath("//a[@href]")
        except:
            return
        for elem in elems:
            try:
                link = elem.get_attribute("href")
            except:
                continue
            if (validators.url(link) == True and filter_file(link) != 'x' and link not in self.have_visit):
                print('add', link)
                extract_queue.append(link)
                self.have_visit.add(link)

        for elem in extract_queue:
            self.SearchCallAPI(elem)
            if self.isFound == RequestStatus.Finish:
                return
        self.BFS_queue.extend(extract_queue)


if __name__ == "__main__":
    # Call jpype, 加入(建立)環境、將jar檔拉入環境
    if not jpype.isJVMStarted():
        jpype.startJVM(jvm_path, "-ea",
                       "-Djava.class.path=%s" % jar_path, convertStrings=False)

    Evaluation_API = jpype.JClass(
        'nculab.widm.event.source.page.discovery.Evaluation')

    # 匯入網址檔案(xlsx檔)
    df = pd.read_excel("Task Information.xlsx")

    for (_, seed_ID, seed_URL) in df.itertuples(name=None):
        ''' 
        Loop every URL in Dataset, and recursively finds URL true or false
        '''
        print("--- Current url : ", seed_URL, " ---")
        
        S = Search(seed_ID, seed_URL)


    print("Done")

    Evaluation_API.main(['--test-version', test_version,
                         '--output-file', './output/' + test_version + '_output.txt'])
    jpype.shutdownJVM()
