# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 16:47:31 2018

@author: Ziqing
"""

from bs4 import BeautifulSoup
import requests
import re
from urllib.parse import urlencode
import json
from hashlib import md5
from multiprocessing import Pool
import time
#from config import *
import config
import os
from json import JSONDecodeError
from requests import RequestException
import pymongo
#获取索引页的HTML信息

client = pymongo.MongoClient(config.MONGO_URL)
db = client[config.MONGO_DB]
def get_page_index(offset,KEYWORD):
   
    data = {
        'offset': offset,
        'format': 'json',
        'keyword': KEYWORD,
        'autoload': 'true',
        'count': 20,
        'cur_tab': 1,
        'from':'search_tab',
            }
    url = "https://www.toutiao.com/search_content/?"+urlencode(data)
    try:
        headers = {"User-Agent":"Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11"}
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print("获取HTML失败")
        return None
#获取索引页的url
def get_page_index_url(html):
    try:
        data = json.loads(html)
        if data and "data" in data.keys():
            for item in data.get("data"):
                
                yield item.get("article_url")
    except JSONDecodeError:
        pass
        

def get_page_second(url):
    
    headers = {"User-Agent":"Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11"}
    try:
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print("获取详情页失败")
        return None


def get_page_second_url(item,url):
    headers = {"User-Agent":"Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11"}
    soup = BeautifulSoup(item,'lxml')
    title = soup.select('title')[0].get_text()
    print(title)
    image = re.compile('gallery: JSON.parse\("(.*?)"\),',re.S)
    reult = re.search(image,item)
    if reult:
      
        data = json.loads(reult.group(1).replace("\\",""))
        
        if data and "sub_images" in data.keys():
            sub_image = data.get("sub_images")
            images = [item.get('url') for item in sub_image]
          
            for image_to in images:
                time.sleep(1)
                download_photo(image_to,headers,title)
            return {
                    "title":title,
                    "url":url,
                    "iamges":images            
                    }
def download_photo(image,headers,title):
    print("正在下载:",image)
    try:
        response = requests.get(image,headers=headers)
        if response.status_code == 200:
            write_filed(response.content,title)
        return None
    except:
        print("下载失败")
        return None
    
def write_filed(content,title):
    if not os.path.exists(title):  #如果文件夹不存在就创建
        os.mkdir(title)
    file_path = '{0}/{1}.{2}'.format(title,md5(content).hexdigest(),'jpg')
    if not os.path.exists(file_path):
        with open(file_path,'wb') as f:
            f.write(content) 
            f.close()
            
def sava_to_mongodb(result):
    if db[config.MONGO_TABLE].insert(result):
        print("存储数据到数据库成功")
        return True
    return False
    
    
#主函数
def get_page_main(offset,KEYWORD=config.KEYWORD):
    html = get_page_index(offset,KEYWORD)
   
    for url in get_page_index_url(html): 
        item = get_page_second(url)
        if item:
            result = get_page_second_url(item,url)
            if result:
                sava_to_mongodb(result)
                

if __name__ == "__main__":
    pool = Pool(3)
    for i in range(config.GROUP_START, config.GROUP_END + 1):
        result = pool.apply_async(get_page_main,(i,))
    result.wait()
    pool.close()
    pool.join()
    


























































