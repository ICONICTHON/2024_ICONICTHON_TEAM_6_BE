import os, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
uri = os.environ.get("MONGODB_URI")
client = MongoClient(uri)
db = client.get_database(os.environ.get("MONGO_DATABASE"))
collection = db['article']

def article_image(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--ignore-certificate-errors')
    # Chrome WebDriver 설정 (경로를 자신의 환경에 맞게 변경)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    # 페이지가 로드되고 동적 콘텐츠가 로드될 시간을 기다림
    time.sleep(2)
    
    try:
        page = driver.page_source
        soup = BeautifulSoup(page, 'html.parser')
        img_tag = soup.select_one('.se_viewArea a img')
        img_url = img_tag['src'] if img_tag else None
        if img_url is not None:
            existing = collection.find_one({'url': url})
            if existing:
                # 기존 문서에 img_url을 추가
                collection.update_one({'url': url}, {'$set': {'img': img_url}})
                
    except Exception as e:
        print(f"이미지 추출할 수 없습니다: {e}")
    
    finally:
        driver.quit()  # 드라이버 종료

# 함수 호출 위치 조정
if __name__ == '__main__':
    url_documents = collection.find({}, {'url': 1, '_id': 0})
    
    for url_document in url_documents:
        if 'url' in url_document:
            url = url_document['url']
            article_image(url)
