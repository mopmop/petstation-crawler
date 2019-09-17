# _*_ coding: utf-8 _*_

"""
test.py
"""

import re
import sys
import spider
import logging
import datetime
import requests
from bs4 import BeautifulSoup

requests.packages.urllib3.disable_warnings()

search_url = "https://www.petstation.jp/animal_list.php?_search_animal__animal_search__species=2&_search_shop_info__animal_search__shop_address2=9&l1_s="


class MyFetcher(spider.Fetcher):
    """
    重写spider.Fetcher类，可自定义初始化函数，这里必须重写父类中的url_fetch函数
    """

    def url_fetch(self, priority: int, url: str, keys: dict, deep: int, repeat: int, proxies=None):
        """
        定义抓取函数，注意参见父类中对应函数的参数和返回值说明
        """
        response = requests.get(url, proxies=proxies, verify=False, allow_redirects=True, timeout=(3.05, 10))
        response.raise_for_status()
        return 1, (response.status_code, response.url, response.content.decode('utf-8', errors="replace")), 1


class MyParser(spider.Parser):
    """
    重写spider.Parser类，可自定义初始化函数，这里必须重写父类中的htm_parse函数
    """

    def __init__(self, max_deep=0):
        """
        初始化函数
        """
        spider.Parser.__init__(self)
        self._max_deep = max_deep
        return

    def htm_parse(self, priority: int, url: str, keys: dict, deep: int, content: object):
        """
        定义解析函数，解析抓取到的content，生成待抓取的url和待保存的item
        """
        status_code, url_now, html_text = content
        soup = BeautifulSoup(html_text, "html.parser")
        table = soup.table
        if "animal_list" in url:
            print("list")
            headers = table.find_all("h3")
            url_list = []
            for h in headers:
                url_list.append((f'https://www.petstation.jp/{h.a["href"]}', keys, priority + 1))

            if len(headers) > 0:
                offset = url[url.rfind('=') + 1:]
                offset = int(offset) + 10
                print(offset)
                url_list.append((f'{search_url}{offset}', keys, priority + 1))
            print(url_list)
            return 1, url_list, None
        else:
            tds = table.find_all("td")
            kind = format_text(tds[0].text)
            price = format_text(tds[1].text)
            gender = format_text(tds[2].text)
            color = format_text(tds[3].text)
            birthday = format_text(tds[4].text)
            cert = format_text(tds[5].text)

            item = {
                "url": url,
                "kind": kind,
                "price": price,
                "gender": gender,
                "color": color,
                "birthday": birthday,
                "cert": cert,
                "datetime": datetime.datetime.now()
            }

            return 1, [], item


class MySaver(spider.Saver):
    """
    重写spider.Saver类，可自定义初始化函数，这里必须重写父类中的item_save函数
    """

    def __init__(self, save_pipe=sys.stdout):
        """
        初始化函数
        """
        spider.Saver.__init__(self)
        self._save_pipe = save_pipe
        return

    def item_save(self, priority: int, url: str, keys: dict, deep: int, item: object):
        """
        定义保存函数，将item保存到本地文件或者数据库
        """
        if item is not None:
            self._save_pipe.write(",".join([str(item[col]) for col in item]))
            self._save_pipe.write("\n")
            self._save_pipe.flush()
        return 1, None


class MyProxies(spider.Proxieser):
    """
    重写spider.Proxieser类，可自定义初始化函数，这里必须重写父类中的proxies_get函数
    """

    def proxies_get(self):
        """
        获取代理，并返回给线程池
        """
        response = requests.get("http://xxxx.com/proxies")
        proxies_list = [{"http": "http://%s" % ipport, "https": "https://%s" % ipport} for ipport in
                        response.text.split("\n")]
        return 1, proxies_list


def format_text(text):
    return ' '.join(text.split())


def test_spider():
    """
    测试函数
    """
    # 初始化 fetcher / parser / saver / proxieser
    fetcher = MyFetcher(sleep_time=0, max_repeat=1)
    parser = MyParser(max_deep=10)
    saver = MySaver(save_pipe=open("cats.txt", "w"))
    # proxieser = MyProxies(sleep_time=5)

    # 定义url_filter
    url_filter = spider.UrlFilter(white_patterns=(re.compile(r"^http[s]?://(www\.)?petstation\.jp"),), capacity=None)

    # 定义爬虫web_spider
    web_spider = spider.WebSpider(fetcher, parser, saver, proxieser=None, url_filter=url_filter, queue_parse_size=-1,
                                  queue_save_size=-1)
    # web_spider = spider.WebSpider(fetcher, parser, saver, proxieser=proxieser, url_filter=url_filter, queue_parse_size=100, queue_proxies_size=100)

    # 添加起始的url
    web_spider.set_start_url(f'{search_url}0', priority=0,
                             keys={"type": "index"}, deep=0)

    # 开启爬虫web_spider
    web_spider.start_working(fetcher_num=40)

    # 等待爬虫结束
    web_spider.wait_for_finished()
    return


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s\t%(levelname)s\t%(message)s")
    test_spider()
