# -*- coding:utf-8 -*-
from bs4 import BeautifulSoup
from os.path import isfile, join
import os
import sys
import subprocess
import PIL.Image as Image
from threading import Thread
import json
from urllib.parse import urlparse
from urllib import parse
import time
import random
from xml.dom import minidom
import shutil

def resolve_url(content, origin=None):
    # cube = content.cube
    url = content.get('url')
    if "?" in url:
        url = url.split('?')[0]
    if url.startswith('http'):
        return url
    if '720yun.com' in origin:
        url = str.replace(url, "%$cdnDomain", "https://ssl-panoimg")
        url = str.replace(url, "%/", ".720static.com/")
    if 'quanjing.com' in origin:
        url = url.replace('%$mypath%', origin)
    if 'autohome.com.cn' in origin:
        # https://panovr.autoimg.cn/pano/pub/aa/e2g/519/u/l2/2/l2_u_2_1.jpg
        url = url.replace('%$tileserver%', 'https://panovr.autoimg.cn/pano/pub')
    if url.startswith('http'):
        return url
    if origin != None:
        if origin.startswith('http'):
            parsed_url = urlparse(origin)
            host = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_url)
            if url.startswith('/'):
                return host + url
            else:
                file = origin.split('/')[-1]
                if '.' in file:
                    start_url = origin[:-(len(file))]
                    return start_url + url
                else:
                    param = origin.split('?')[-1]
                    start_url = origin[:-(len(file))]
                    return (start_url + url).replace('?', '/')
    return url

def resolve_id(content):
    xml_soup = BeautifulSoup(content, 'lxml')
    if xml_soup.scene != None:
        name = xml_soup.scene.get('name')
        if name != None:
            return name
    return "tour"

surfaces = ["b", "d", "f", "l", "r", "u"]

# 构建基于规则的新方法
def download_new_images(path, image_width, image_height, l_width, referer, base_url):

    count = int(image_width)/int(l_width) + 1 + 1
    count_height = int(image_height)/int(l_width) + 1 + 1
    if int(image_width)%int(l_width) == 0:
        count -= 1
    if int(image_height)%int(l_width) == 0:
        count_height -= 1
    # patterns = str.split(pattern, '/')
    if '%s' in base_url:
        start = base_url.split('%s')[0]
    else:
        start = base_url.split('%')[0]
    global threads
    for surface in surfaces:
        for dir in range(1, int(count_height)):
            for file in range(1, int(count)):
                file_name = str.replace(base_url, "%s", surface)
                file_name = str.replace(file_name, "%00v", full_number(dir, 3))
                file_name = str.replace(file_name, "%0v", full_number(dir, 2))
                file_name = str.replace(file_name, "%v", str(dir))
                file_name = str.replace(file_name, "%00h", full_number(file, 3))
                file_name = str.replace(file_name, "%0h", full_number(file, 2))
                file_name = str.replace(file_name, "%h", str(file))
                url = file_name
                file_name = file_name[len(start):]
                output = os.path.join(path, file_name)
                if "?" in output:
                    output = str.split(output, "?")[0]
                if os.path.exists(output):
                    continue
                dir_name = os.path.dirname(output)
                dir_path = os.path.join(path, dir_name)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                t = Thread(target=download_image, args=[referer, url, output])
                t.start()
                threads.append(t)
                if len(threads) < 80:
                    continue
                for t in threads:
                    t.join()
                threads = []
    for t in threads:
        t.join()
    threads = []

import downloader
def download_image(referer, url, output):
    downloader.download_image(referer, url, output)

def combine_image(path, l_width, l_height, image_path):
    base_dir = os.path.dirname(image_path)
    if os.path.isfile(image_path):
        return
    if not os.path.isdir(base_dir):
        os.makedirs(base_dir)
    name_path = path
    to_image = Image.new('RGB', (int(l_width), int(l_height)))
    names = [f for f in os.listdir(name_path) if os.path.isdir(os.path.join(name_path, f))]
    v_offset = 0
    tile_width = 0
    for dir_name in sorted(names):
        file_path = os.path.join(name_path, dir_name)
        image_files = [f for f in os.listdir(file_path) if (os.path.isfile(os.path.join(file_path, f)) and (not f.startswith('.')))]
        h_offset = 0
        for image_file in sorted(image_files):
            image_file_path = os.path.join(file_path, image_file)
            try:
                from_image = Image.open(image_file_path)
                if h_offset == 0 and tile_width == 0:
                    width, height = from_image.size
                    tile_width = width
                to_image.paste(from_image, (h_offset, v_offset))
            except Exception:
                print(image_file_path + '图片异常，请修复该图片后，将路径拖入工具进行后续操作')
            h_offset += tile_width
        v_offset += tile_width
    to_image.save(image_path)

# 针对命名规则填充0
def full_number(num, digit):
    num_str = str(num)
    digit_int = int(digit)
    if len(num_str) >= digit_int:
        return num_str
    for index in range(digit_int - len(num_str)):
        num_str = '0' + num_str
    return num_str

def combine_downloaded_images(pattern, path, image_width, image_height, l_width):
    # return
    count = int(image_width)/int(l_width) + 1 + 1
    count_height = int(image_height)/int(l_width) + 1 + 1
    if int(image_width)%int(l_width) == 0:
        count -= 1
    if int(image_height)%int(l_width) == 0:
        count_height -= 1
    patterns = str.split(pattern, '/')
    level = ""
    if len(patterns) > 1:
        level = patterns[1]
    else:
        combine_image(path, image_width, image_height, image_path=os.path.join(path, 'combined.jpg'))
        return
    dir_path = os.path.join(path, level)
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    for surface in surfaces:
        # 创建正方形图片
        image_path = os.path.join(path, level + '/pano_' + surface + '.jpg')
        if os.path.exists(image_path):
            continue
        to_image = Image.new('RGB', (int(image_width), int(image_width)))
        for dir in range(1, int(count)):
            for file in range(1, int(count)):
                file_name = str.replace(pattern, "%s", surface)
                file_name = str.replace(file_name, "%00v", full_number(dir, 3))
                file_name = str.replace(file_name, "%0v", full_number(dir, 2))
                file_name = str.replace(file_name, "%v", str(dir))
                file_name = str.replace(file_name, "%00h", full_number(file, 3))
                file_name = str.replace(file_name, "%0h", full_number(file, 2))
                file_name = str.replace(file_name, "%h", str(file))
                if "?" in file_name:
                    file_name = str.split(file_name, "?")[0]
                file_path = os.path.join(path, file_name)
                if not os.path.exists(file_path):
                    continue
                try:
                    form_image = Image.open(file_path)
                    to_image.paste(form_image, ((file-1) * int(l_width), (dir-1) * int(l_width)))
                except Exception:
                    print(file_path + '图片异常，请修复该图片后，将路径拖入工具进行后续操作')
        to_image.save(image_path)

threads = []
def parse_realsee(content, url, path):
    json_object = json.loads(content)
    # print(json_object)
    keys = ['up', 'down', 'left', 'right', 'front', 'back']
    if 'work' in json_object:
        work = json_object['work']
        if 'panorama' in work:
            panorama = work['panorama']
            base_url = panorama['base_url']
            if 'list' in panorama:
                scenes = panorama['list']
                convert_threads = []
                for scene in scenes:
                    name = scene['index']
                    dir_path = path
                    threads = []
                    for key in keys:
                        if key in scene:
                            image_url = scene[key]
                            file_name = str.split(image_url, base_url)[-1]
                            output = os.path.join(path, file_name)
                            if "?" in output:
                                output = str.split(output, "?")[0]
                            dir_name = os.path.dirname(output)
                            dir_path = os.path.join(path, dir_name)
                            if not os.path.exists(dir_path):
                                os.makedirs(dir_path)
                            if os.path.exists(output):
                                continue
                            t = Thread(target=download_image, args=[url, image_url, output])
                            t.start()
                            threads.append(t)
                            
                    for t in threads:
                        t.join()
                    threads = []
                    
                    t_convert = Thread(target=convert, args=[dir_path, os.path.join(dir_path, '../'), str(name)])
                    t_convert.start()
                    convert_threads.append(t_convert)
                for t in convert_threads:
                    t.join()

# 合并整个流程
def resolve(string, path=None, level=None, all=True):
    if string == '':
        return
    # 判断本地模式，如果有6个面的碎图片，则直接进行拼接
    if os.path.isdir(string):
        return

    start_time = time.time()
    url = downloader.judge_url(string)
    if url == None:
        return

    if path == None:
        execute_path = os.getcwd()
        path = os.path.join(execute_path, 'output')
        
    if url.startswith('http'):
        parsed_url = urlparse(url)
        host = '{uri.netloc}'.format(uri=parsed_url)
        path = os.path.join(path, host)
        if not os.path.exists(path):
            os.makedirs(path)

    if url.startswith('http') and (not 'realsee' in url) and (not '720yun.com' in url):
        # 用于处理所有非如视和720yun的链接，首先必须拿到xml地址
        origin = downloader.parse_url(url)
        base_url = downloader.parse_base_url(url)
        if base_url == None:
            resolve_tour(origin, path, all, url)
        else:
            scenes = downloader.fetch_tour_scenes(origin, path, url)
            resolve_scenes(base_url, path, scenes, all)
        time.sleep(3)
        return
    
    content = downloader.parse_content(url)
    if content == None:
        return
    
    if 'realsee.com' in url:
        parse_realsee(content, url, path)
        time.sleep(3)
        return

    origin = url
    if url.startswith('/'):
        path = origin
    
    xml_soup = BeautifulSoup(content, 'lxml')
    scenes = xml_soup.findAll('scene')

    for scene in scenes:
        name = resolve_id(str(scene))
        #  此规则待重构，仅720yun适用
        scene_name = str.split(name, 's_')[0]
        if scene_name in url:
            resolve_scene(scene, path, level, origin)
            continue
        if all == False:
            continue
        resolve_scene(scene, path, level, origin)
    end_time = time.time()
    duration = int(end_time - start_time)
    print('\n\nAll it last ' + str(duration) + ' seconds')
    time.sleep(3)

from urllib.parse import urljoin  # Python3
# 通用的通过tour.xml文件来获取到直接的配置
def resolve_tour(url, path, all=True, referer=None):
    scenes = downloader.fetch_tour_scenes(url, path, referer)
    if scenes == None or len(scenes) == 0:
        # 兼容云创规则使用
        urls = downloader.fetch_tour_urls(url)
        if len(urls) == 0:
            return
        for scene_url in urls:
            temp_url = scene_url.get('url')
            if not 'tour.xml' in temp_url:
                continue
            if temp_url.startswith('http'):
                resolve_tour(temp_url, path, all)
            else:
                tour_url = urljoin(url, temp_url)
                resolve_tour(tour_url, path, all)
        return
    resolve_scenes(url, path, scenes, all)

# 需要兼容quanjing.com传入原网址的参数
def resolve_scenes(url, path, scenes, all=True):
    if 'quanjing.com' in url or 'sigoo.com' in url:
        path = os.path.join(path, os.path.basename(url))
    for scene in scenes:
        resolve_scene(scene, path, None, url)
        if all == False:
            break

def download_simple_images(url, path, origin):
    print("Start downloading " + path)
    for surface in surfaces:
        image_url = url.replace('%s', surface)
        image_name = image_url.split('/')[-1]
        file_path = os.path.join(path, image_name)
        download_image(origin, image_url, file_path)
    convert(path, path, 'pano')


def convert(path, output, name):
    print(path)

def resolve_scene(scene, path, level=None, url=None):
    scene_name = resolve_id(str(scene))
    images = scene.findAll('image')
    dir_path = path
    if not os.path.exists(url):
        dir_path = os.path.join(path, scene_name)
    resolve_images(images, dir_path, level, url)

def resolve_images(images, dir_path, level=None, url=None):
    if len(images) == 1:
        image = images[0]
        levels = image.findAll('level')
        if len(levels) == 0:
            cube = image.cube
            image_url  = resolve_url(cube, url)
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)
            download_simple_images(image_url, dir_path, url)
            return

    for image in images:
        image_type = image.get('type')
        if not image_type == 'CUBE' and (image_type != 'CYLINDER'):
            continue
        cube = image.cube
        tilesize = image.get('tilesize')
        levels = image.findAll('level')
        if len(levels) == 0:
            continue
        if level == None or level == "max":
            count = len(levels)
            if count < 4:
                l = levels[0]
            else:
                l = levels[-3]
            download_all(l, dir_path, tilesize, url)
            continue
        if level == 'min':
            l = levels[-1]
            download_all(l, dir_path, tilesize, url)
            continue
        for l in levels:
            l_width = l['tiledimageheight']
            l_height = l['tiledimageheight']
            cubes = l.findAll('cube')
            for cube in cubes:
                pattern = str(cube['url'])
                if level == "all":
                    download_simple(cube, l_width, l_height, dir_path, tilesize, url)
                elif '/' + level + '/' in pattern:
                    download_simple(cube, l_width, l_height, dir_path, tilesize, url)
                    continue

def download_simple(cube, l_width, l_height, dir_path, tilesize, url):
    base_url = resolve_url(cube, url)

    if base_url.startswith('http') :
        print('Start downloading ' + dir_path)
        download_new_images( dir_path, l_width, l_height, tilesize, url, base_url)
    elif base_url == None or base_url == '':
        return
    else:
        dir_path = os.path.join(dir_path, cube['url'].split('%')[0])

    pattern = str.split(base_url, '%s/')[-1]
    pattern = '%s/'+pattern
    if not os.path.exists(os.path.join(dir_path, 'pano_u.jpg')):
        print('Start combining images ' + dir_path)
        combine_downloaded_images(pattern, dir_path, l_width, l_height, tilesize)

    components = pattern.split('/')
    if len(components) < 2:
        return
    pano_dir = os.path.join(dir_path, components[1])
    convert(pano_dir, pano_dir, 'pano')

def download_all(l, dir_path, tilesize, url):
    l_width = l['tiledimagewidth']
    l_height = l['tiledimageheight']
    cubes = l.findAll('cube')
    if len(cubes) == 0:
        cubes = l.findAll('cylinder')
    for cube in cubes:
        download_simple(cube, l_width, l_height, dir_path, tilesize, url)

if __name__ == '__main__':
    argv = sys.argv
    if len(argv) > 1:
        url = argv[1]
        level = None
        path = None
        if len(argv) > 3:
            level = argv[3]
        if len(argv) > 2:
            path = argv[2]
        resolve(url, path, level)
    else:
        # path = input('Please input the url!\n')
        path = input('请输入或粘贴要抓取的全景图链接!\n')
        resolve(path)