# -*- coding:utf-8 -*-
import os
import requests
import random
from urllib.parse import urlparse
from pyaria2 import Aria2RPC
from bs4 import BeautifulSoup
import re
from urllib import parse
import time

ua = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36Name', 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1']
def download_image(referer, url, output):
    if not url.startswith('http'):
        return
    file_dir = os.path.dirname(output)
    file_name = output.split('/')[-1]
    rpc = Aria2RPC()
    options = {"dir": file_dir, "out": file_name}
    try:
        rpc.addUri([url], options= options)
        time.sleep(5)
    except Exception:
        parsed_url = urlparse(referer)
        origin = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_url)
        headers = {'referer': referer, 'Origin': origin, 'User-Agent': random.choice(ua)}
        try:
            # 部分域名需要关闭ssl验证
            # response = requests.get(url, headers=headers, stream=True, verify=False)
            response = requests.get(url, headers=headers, stream=True)
            if response.status_code != 200:
                print(url + '下载失败。 ' + str(response.status_code))
                return
            with open (output, 'wb') as f:
                f.write(response.content)
        except Exception as error:
            print(url + '下载失败。 ')
            print(error)
            return
 
def download_file(url, output):
    dir_path = os.path.dirname(output)
    file_path = output
    if os.path.isdir(output):
        file_name = url.split('/')[-1]
        file_path = os.path.join(output, file_name)
    if not os.path.isdir(dir_path):
        try:
            os.makedirs(dir_path)
        except Exception:
            return False
    if os.path.exists(file_path):
        return True
    # 判断完路径才开始请求 
    headers = {
        'User-Agent': random.choice(ua)}
    res = requests.get(url, headers=headers)
    if not res.status_code == 200:
        print(url + ' download failed!')
        return False
    with open(file_path, 'wb') as f:
        f.write(res.content)
        return True

def parse_content(url):
    # 判断是否本地文件夹
    if os.path.isdir(url):
        file_path = os.path.join(url,'tour.xml')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    # 二次判断是否链接
    if judge_url(url) == None:
        return None
    headers = {
        'User-Agent': random.choice(ua)}
    response = requests.get(url, headers=headers)
    # print(response.text)
    soup = BeautifulSoup(response.text, 'lxml')
    scripts = soup.body.findAll('script')
    if '720yun.com' in url:
        matchs = re.search('<\?xml.*/krpano>', str(scripts))
        if matchs == None:
            if '/u/' in url:
                user_id = url.split('/')[-1]
                user_url = 'https://apiv4.720yun.com/author/' + user_id
                headers['app-key'] = 'eByjUyLDG2KtkdhuTsw2pY46Q3ceBPdT'
                # headers['cookie'] = '720yun_v8_session=6Z7pXd2PBA0NWybMRYLDJlaELY0MYz8ySOmvzmXyrkQV3o98xKwOrgG5jzvm1eE4'
                headers['referer'] = url
                headers['origin'] = 'https://720yun.com'
                res = requests.get(user_url, headers=headers)
                result = res.json()
                productXml = result['data']['productXml']
                return productXml
        content = matchs.group()
        return content

    for script in scripts:
        if 'realsee.com' in url:
            if 'window.__module__data' in str(script):
                content = str.split(str(script), 'window.__module__data =')[-1]
                content = str.split(content, ';;')[0]
                return content
    return None

# 扩写这个方法，用来适配大部分网站
def parse_url(url):
    if 'krpano100.com' in url:
        tour = url.replace('/tour/', '/tour/tour.xml.php?view=')
        tour = tour.replace('?Scene=', '&startscene=')
        return tour
    elif 'autohome.com.cn' in url:
        # https://pano.autohome.com.cn/car/pano/
        # https://pano.autohome.com.cn/car/pano/25893#pvareaid=2023606
        link_id = url.split('?')[0]
        link_id = link_id.split('#')[0]
        return link_id + '.xml'
    elif 'vr.ipanda.com' in url:
        link_id = os.path.join(os.path.dirname(url), 'main.xml')
        return link_id
    elif 'quanjing.com' in url:
        return 'https://vr.quanjing.com/Scripts/Vr/tour.xml'
    elif 'panovtour.com' in url:
        link_id = url.split('?')[0]
        link_id = link_id.split('#')[0]
        link_id = os.path.basename(link_id)
        return 'http://www.panovtour.com/view/tour.xml.php?view=' + link_id
    elif '720.so' in url:
        view_id = url.split('?')[0]
        view_id = view_id.split('/')[-1]
        tour = 'https://720.so/tour/tour.xml.php?view=' + view_id
        return tour

    headers = {
        'User-Agent': random.choice(ua)}
    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, 'lxml')
    scripts = soup.body.findAll('script')
    for script in scripts:
        if 'sigoo.com' in url:
            if 'window.__PANO__ =' in str(script):
                matchs = re.search('xml:".*', str(script))
                content = matchs.group()
                vr_path = content.split('"')[-2]
                return vr_path
    return url

hosts = ['quanjing.com']
def parse_base_url(url):
    contained = False
    for host in hosts:
        if host in url:
            contained = True
    if contained == False:
        return None
    headers = {
        'User-Agent': random.choice(ua)}
    response = requests.get(url, headers=headers)
    response.encoding = response.apparent_encoding
    html = response.text
    if 'quanjing.com' in url:
        vurls = re.findall('vrurl="([^<>]+?)"', html)
        if len(vurls) != 0:
            return vurls[0]
    return None

def fetch_hdr_images(url):
    headers = {
        'User-Agent': random.choice(ua)}
    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, 'lxml')
    print(soup.body)

def fetch_tour_scenes(url, path, referer=None):
    headers = {
        'User-Agent': random.choice(ua), "Referer": referer}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print('error' + str(response.status_code))
        print(response.url)
        return None
    # 需要准备带有header信息
    xml_soup = BeautifulSoup(response.text, 'lxml')
    if not os.path.isdir(path):
        os.makedirs(path)
    with open(os.path.join(path, 'tour.xml'), 'w', encoding='utf8') as f:
        f.write(response.text)
    scenes = xml_soup.findAll('scene')
    if len(scenes) != 0:
        return scenes
    images = xml_soup.findAll('image')
    index = 1
    for image in images:
        scene = '<scene name="scene_' + str(index) + '">' + str(image) + '</scene>'
        scene = BeautifulSoup(scene, 'lxml')
        scenes.append(scene)
        index += 1
    return scenes

def fetch_tour_urls(url):
    headers = {
        'User-Agent': random.choice(ua)}
    response = requests.get(url, headers=headers)
    # 需要准备带有header信息
    xml_soup = BeautifulSoup(response.text, 'lxml')
    scenes = xml_soup.findAll('include')
    return scenes

# re.match(r'^https?:/{2}\w.+$', url)
def judge_url(string):
    if os.path.exists(string):
        return string
    try_path = os.path.join(os.getcwd(), string)
    if os.path.exists(try_path):
        return try_path
    pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    urls = re.findall(pattern,string)
    if len(urls) == 0:
        return None
    return urls[0]