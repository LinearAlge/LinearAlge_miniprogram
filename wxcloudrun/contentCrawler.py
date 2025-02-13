import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
from readability import Document  # 需要安装readability-lxml
import re
def parse_detail_page(url):
    try:
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'  # 确保响应内容使用 UTF-8 编码
        doc = Document(response.text)
        
        # 使用Readability自动提取正文
        cleaned_html = doc.summary()
        
        # 进一步清洗（移除无用标签）
        soup = BeautifulSoup(cleaned_html, 'html.parser')
        for tag in soup(['script', 'style', 'header', 'footer', 'nav']):
            tag.decompose()
        
        # 转换相对链接为绝对链接
        for tag in soup.find_all(['a', 'img']):
            if tag.get('href'):
                tag['href'] = urljoin(url, tag['href'])
                tag['data-href'] = tag['href']  # 添加 data-href 属性
            if tag.get('src'):
                tag['src'] = urljoin(url, tag['src'])
        
        # 安全过滤（移除危险属性和事件）
        SAFE_ATTRS = {'src', 'href', 'alt', 'title', 'width', 'height', 'colspan', 'rowspan'}
        for tag in soup.find_all(True):
            tag.attrs = {k: v for k, v in tag.attrs.items() if k in SAFE_ATTRS}
            # if tag.name == 'img':
            #     tag['style'] = 'display: block !important;max-width: 100% !important;height: auto !important;margin: 20px auto;border-radius: 8px;box-shadow: 0 4px 12px rgba(0,0,0,0.1);'  # 添加基础样式
            # elif tag.name == 'p':
            #     tag['style'] = 'margin: 1em 0 !important; font-family: -apple-system, sans-serif;'  # 为段落添加样式
            # elif tag.name == 'a':
            #     tag['style'] = 'color: #1E90FF;text-decoration: underline;'
            
        def traverse(node):
            result = {
                'name': node.name,
                'attrs': dict(node.attrs),
                'children': []
            }
            for child in node.children:
                if isinstance(child, str):
                    result['children'].append({
                        'type': 'text',
                        'text': child
                    })
                else:
                    result['children'].append(traverse(child))
            return result
        
        structured_content = [traverse(child) for child in soup.body.children if child.name]
        
        # from bs4.element import NavigableString
        # for element in soup.find_all():
        #     if len(element.contents) > 0:
        #         merged = []
        #         current = []
        #         for child in element.contents:
        #             if isinstance(child, NavigableString):
        #                 current.append(child.strip())
        #             else:
        #                 if current:
        #                     merged.append(' '.join(current))
        #                     current = []
        #                 merged.append(child)
        #         if current:
        #             merged.append(' '.join(current))
                
        #         # 清空原有内容并添加合并后的内容
        #         element.clear()
        #         for item in merged:
        #             if isinstance(item, str):
        #                 element.append(NavigableString(item))
        #             else:
        #                 element.append(item)
        
        # # 新增：压缩HTML空白
        # html_str = str(soup)
        # html_str = re.sub(r'\n\s*', ' ', html_str)  # 替换换行和连续空格
        # html_str = re.sub(r'(?<=>)\s+(?=<)', '', html_str)  # 移除标签间空白
        
        # html_str = re.sub(r'\s+', ' ', str(soup))  # 替换所有连续空白为单个空格
        
        # # 新增：移除标签间的空白（如 </span> <span> 之间的空格）
        # html_str = re.sub(r'(?<=>)\s+(?=<)', '', html_str)
        
        return {
            'title': doc.title(),
            'content': str(soup),
            'source_url': url
        }
    except Exception as e:
        return {'error': str(e)}

if __name__ == "__main__":
    data = parse_detail_page(
        "http://www.cse.zju.edu.cn/2025/0113/c39322a3011298/page.htm",
    )
    print(json.dumps(data, ensure_ascii=False, indent=2))