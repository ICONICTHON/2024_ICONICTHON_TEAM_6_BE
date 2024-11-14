import requests, re, os, pprint, time, psutil, spacy
from selenium import webdriver
from browsermobproxy import Server
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv
from bson.objectid import ObjectId
from transformers import PreTrainedTokenizerFast, BartForConditionalGeneration
import torch

#device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
tokenizer = PreTrainedTokenizerFast.from_pretrained('digit82/kobart-summarization')
model = BartForConditionalGeneration.from_pretrained('digit82/kobart-summarization')

def summarize(text):
    max_length = 1024  # 모델의 최대 입력 길이에 맞게 설정
    step_size = max_length - 50  # 약간 중첩되게 나누기 위해 step 설정
    summary_all = []    
    # 텍스트를 max_length 크기로 나누어서 처리
    for i in range(0, len(text), step_size):
        chunk = text[i:i + max_length]
        raw_input_ids = tokenizer.encode(chunk)
        input_ids = [tokenizer.bos_token_id] + raw_input_ids + [tokenizer.eos_token_id]
        
        # 모델이 처리할 수 있도록 텐서 변환
        summary_ids = model.generate(
            torch.LongTensor([input_ids]), num_beams=8, max_length=512, eos_token_id=1, length_penalty=1.5, no_repeat_ngram_size=3
        )
        # 요약 결과를 디코딩 후 리스트에 추가
        summary = tokenizer.decode(summary_ids.squeeze().tolist(), skip_special_tokens=True)
        summary_all.append(summary)

    # 요약 조각들을 하나로 합치기
    final_summary = ' '.join(summary_all)
    
    return final_summary

def process_kill(name):
    """중복 실행중인 프로세스 종료"""

    for proc in psutil.process_iter():
        if proc.name() == name:
            proc.kill()

def capture_network_traffic(url):
    """프록시 서버 시작 및 네트워크 트래픽 캡쳐"""

    server = Server(path="/home/alexkim/Downloads/browsermob-proxy-2.1.4/bin/browsermob-proxy")
    server.start()
    time.sleep(1)
    proxy = server.create_proxy()
    time.sleep(1)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--proxy-server={0}".format(proxy.proxy))
    chrome_options.add_argument('--ignore-certificate-errors')

    driver = webdriver.Chrome(options=chrome_options)

    proxy.new_har("naver_page", options={'captureContent': True}) # options={'captureContent': True} https://github.com/lightbody/browsermob-proxy

    driver.get(url)
    time.sleep(3)
    for i in range(5):
        try:
            more_button = driver.find_element("css selector", '.btn_lst_more')
            driver.execute_script("arguments[0].scrollIntoView(true);", more_button)
            time.sleep(1)  # 스크롤 후 약간의 대기 시간
            more_button.click()
            time.sleep(3)  # 데이터를 로드할 시간을 줍니다.
        except Exception as e:
            print(f"더 이상 로드할 데이터가 없습니다. (에러: {e})")
            break
    driver.quit()
    server.stop()
    # 트래픽 분석
    har_data = proxy.har

    # 브라우저 종료 및 proxy 서버 종료
    driver.quit()
    server.stop()

    # XHR 요청 중 JSON 응답을 포함하는 요청 찾기
    xhr_responses = []
    for entry in har_data['log']['entries']:
        # 만약 JSON 형식의 XHR 요청이라면 응답 데이터를 수집합니다.
        if 'json' in entry['response']['content'].get('mimeType', ''):
            xhr_responses.append(entry['response']['content']['text'])
    return xhr_responses

def extract_author(text):
    # 정규 표현식을 사용해 '[다르마 = {기자 이름} 기자]' 형식에서 기자 이름만 추출
    match = re.search(r'\[.*?다르마.*?=\s*(.*?)\s*기자.*?\]', text)
    if match:
        return match.group(1).strip()
    
    return "NULL"

def crawl_news_list(xhr_responses, sports_type):
    """응답 데이터 가공"""
    news_list = []
    for i, response in enumerate(xhr_responses):
        news_links = re.findall(r'a href=\\"(\/viewer\/postView\.naver\?volumeNo=[^"]+)\\"', response)
        for link in news_links:
            url = "https://m.post.naver.com" + link
            news_data = crawl_news(url)
            news_data['sports_type'] = sports_type
            news_list.append(news_data)

    return news_list

def crawl_news(url):
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--ignore-certificate-errors')
    # Chrome WebDriver 설정 (경로를 자신의 환경에 맞게 변경)
    driver = webdriver.Chrome(options=chrome_options)
    # 웹 페이지 로드
    driver.get(url)

    # 페이지가 로드되고 동적 콘텐츠가 로드될 시간을 기다림
    time.sleep(2)

    description = []
    try:
        page = driver.page_source
        soup = BeautifulSoup(page, 'html.parser')
        title = soup.select_one('h3.se_textarea').get_text(strip=True)
        date = soup.select_one('p.se_detail span.se_publishDate').get_text(strip=True)
        elements = soup.select('p.se_textarea')
        for element in elements:
            description.append(element.get_text(separator=' ', strip=True).replace('\xa0', ' '))
        
        text = ' '.join(description)
        # 기자 이름 추출
        author = extract_author(text)

        if len(text) < 400:
            summary = text
        else:
            summary = summarize(text)

        news_data = {'title': title, 'date': date, 'description': text, 'summary': summary, 'url': url, 'author': author}            
            
    except Exception as e:
        print(f"본문을 추출할 수 없습니다: {e}")

    # 브라우저 종료
    driver.quit()
    
    return news_data

def crawl_updated_news(url):
    news_list = []
    response = requests.get(url)
    response.raise_for_status()
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    href_tags = soup.select('ul.list_spot_post._post_list a')
    for tag in href_tags:
        link = tag['href']
        url = "https://m.post.naver.com" + link
        news_data = crawl_news(url)
        news_list.append(news_data)
    
    return news_list


load_dotenv()
uri = os.environ.get("MONGODB_URI")
client = MongoClient(uri)
db = client.get_database(os.environ.get("MONGO_DATABASE"))
collection = db['article']

# 크롤링 후 데이터를 MongoDB에 삽입하는 함수
def insert_and_check_data():
    sports_url = {
        'https://m.post.naver.com/my/series/detail.naver?memberNo=51653576&seriesNo=623989': 'soccer',
        'https://m.post.naver.com/my/series/detail.naver?memberNo=51653576&seriesNo=623990': 'baeball',
        'https://m.post.naver.com/my/series/detail.naver?memberNo=51653576&seriesNo=623991': 'basketball'
    }
    article_result = []
    for url in sports_url:
        upadated_news_list = crawl_updated_news(url)
        article_result.extend(upadated_news_list)
        process_kill("browsermob-proxy")
        xhr_responses = capture_network_traffic(url)
        news_list = crawl_news_list(xhr_responses, sports_url[url])
        article_result.extend(news_list)
    
    # 크롤링한 데이터를 MongoDB에 삽입
    result = collection.insert_many(article_result)

    # 삽입된 데이터 ObjectID 목록 출력 (확인용)
    inserted_ids = result.inserted_ids
    print("Inserted Document IDs:")
    print(inserted_ids)

    # 삽입된 데이터 확인 (갓 삽입된 데이터를 조회)
    print("\nInserted Documents:")
    for doc_id in inserted_ids:
        # 각 ID에 대해 MongoDB에서 문서를 가져와 확인
        document = collection.find_one({"_id": ObjectId(doc_id)})
        pprint.pprint(document)  # 데이터를 보기 좋게 출력
        
    
    

if __name__ == '__main__':
    insert_and_check_data()