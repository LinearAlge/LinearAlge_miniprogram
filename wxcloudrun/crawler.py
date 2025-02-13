import requests
from bs4 import BeautifulSoup
from dateutil import parser
import json
from datetime import datetime
from urllib.parse import urljoin

with open('config.json', 'r', encoding='utf-8') as f:
    site_configs = json.load(f)
    
def crawl_school_news(target_url, max_page=3, keywords=None, max_items=None, start_time=None, end_time=None):
    #print(target_url)
    domain = target_url.split('/')[2]  # 提取域名
    #print(domain)
    config = site_configs.get(domain, {})
    #print(config)
    all_items = []
    current_url = target_url
    total_items = 0
    
    try:
        for _ in range(max_page):
            #print(current_url)
            if not current_url:
                break
            # 发送请求（添加基础反爬策略）
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': current_url
            }
            response = requests.get(current_url, headers=headers, timeout=10)
            response.encoding = 'utf-8'  # 根据网站编码调整
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # 示例：假设通知在class="news-list"的div中，需根据实际网站调整
            news_items = []
            for item in soup.select(config.get('item_selector','')):  # 根据实际CSS选择器修改
                title = item.select_one(config['title_selector'][0]).get(config['title_selector'][1])
                link = item.select_one(config['link_selector'][0]).get(config['link_selector'][1])
                #print(link, type(link))
                # 处理相对链接
                full_link = urljoin(current_url, link)
                # 提取时间（假设时间在span标签内）
                time_str = item.select_one(config['time_selector']).text.strip()
                publish_time = parser.parse(time_str).strftime('%Y-%m-%d')
                source = config.get('source_name')
                news_item = {
                    'title': title,
                    'url': full_link,
                    'publish_time': publish_time,
                    'source': source  # 自定义来源标识
                }
                news_items.append(news_item)
            
            # 过滤逻辑
            if start_time and end_time:
                news_items = filter_by_time(news_items, start_time, end_time)
            
            filtered_items = filter_by_keywords(news_items, keywords) if keywords else news_items
            all_items.extend(filtered_items)
            total_items += len(filtered_items)
            
            if max_items and total_items >= max_items:
                break
            
            next_page_element = soup.select_one(config.get('next_page_selector')[0])
            #print(next_page_element.prettify())
            if next_page_element:
                next_page = next_page_element.get(config.get('next_page_selector')[1])
                #print(next_page)
                current_url = urljoin(current_url, next_page)
            else:
                break
        return {
            'status': 'success',
            'data': all_items,
            'last_crawled': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

# 按关键词过滤   
def filter_by_keywords(items, keywords, match_all=False):
    filtered = []
    keywords = [k.lower() for k in keywords]
    
    for item in items:
        title = item['title'].lower()
        # 匹配逻辑
        if match_all:
            if all(k in title for k in keywords):
                filtered.append(item)
        else:
            if any(k in title for k in keywords):
                filtered.append(item)
                
    return filtered

# 按时间过滤
def filter_by_time(news_items, start_time, end_time):
    filtered_items = []
    for item in news_items:
        publish_time = datetime.strptime(item['publish_time'], '%Y-%m-%d %H:%M:%S')
        if start_time <= publish_time <= end_time:
            filtered_items.append(item)
    return filtered_items

# 测试调用
if __name__ == "__main__":
    start_time = datetime(2024, 10, 1)
    end_time = datetime(2024, 12, 31)
    data = crawl_school_news(
        "http://www.cse.zju.edu.cn/39322/list1.htm",
        keywords = ["控制学院"],
        max_items= 50,
        start_time=start_time,
        end_time=end_time
    )
    print(json.dumps(data, ensure_ascii=False, indent=2))