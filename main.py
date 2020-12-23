import re
import os
import sys
import glob
import jpype
import requests
import subprocess
import pandas as pd
import xlrd
from bs4 import BeautifulSoup
from subprocess import Popen, PIPE, STDOUT
from datetime import datetime
from http import HTTPStatus
import validators

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

# 移除 SSL 認證
requests.packages.urllib3.disable_warnings()

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
        #self.NaiveDFS(self.seed_URL)
        self.NavieBFS(self.seed_URL)

    def SearchCallAPI(self, id, url):
        '''
        根據 id 與 url 去 java 看對不對
        '''
        print('ID : {id} , cost = {cost} {url}'.format(id=str(id), cost = self.cost, url=url))
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
        command.append(str(id))
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
        while(self.isFound != RequestStatus.Finish and self.isFound != RequestStatus.Fail ):
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

            self.SearchCallAPI(self.seed_ID, self.BFS_queue[0])
            self.ExtractLinks(self.BFS_queue[0])
            self.BFS_queue.pop(0)
            
            
    # def NaiveDFS(self, URL):
    #     BFS_queue = self.ExtractLinks(URL)
    #     for i in BFS_queue:
    #         self.SearchCallAPI(self.seed_ID, i)
    #         if(self.isFound):
    #             return
            
    #         self.NaiveDFS(i)
            
    def ExtractLinks(self, url):
        '''
        ExtractLinks
        根據輸入的 URL 搜尋該網頁原始碼中的連結
        '''
        extract_queue = []

        '''
        將該網頁之下的原始碼取出，且設定請求的 timeout，如果超過就放棄
        '''


        try:
            html_page = requests.get(url, verify=False, timeout=5)
            if html_page.status_code != HTTPStatus.OK:
                if url == self.seed_URL:
                    self.isFound = RequestStatus.Fail
                return


        except requests.exceptions.RequestException as e:
            print(e)

            # 超時
            if url == self.seed_URL:
                self.isFound = RequestStatus.Fail
            return


        soup = BeautifulSoup(html_page.text, "html.parser")

        #  抓取 https 與 http 的連結
        result = soup.findAll('a', href=re.compile("(^https?://)"))
        for link in result:
            filtered_url = filter_file(link.get('href'))

            # 檢查是否已走訪
            if (filtered_url != 'x' and link.get('href') not in self.have_visit):
                extract_queue.append(link.get('href'))
                self.have_visit.add(link.get('href'))
            # print(link.get('href'))

        # 抓取同個網域下的連接
        result = soup.findAll('a', href=re.compile("^/"))
        domin_name = get_http_domin_helper(url)
        for link in result:
            filtered_url = filter_file(domin_name + link.get('href'))
            if (filtered_url != 'x' and domin_name + link.get("href") not in self.have_visit):
                extract_queue.append(domin_name + link.get("href"))
                self.have_visit.add(domin_name + link.get("href"))
            #print(domin_name + link.get("href"))

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
