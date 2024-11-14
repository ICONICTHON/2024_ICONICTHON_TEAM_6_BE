import requests, re, os, pprint
from bs4 import BeautifulSoup
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId

sports_page = {2004: 'baseball', 2010: 'soccer', 2016: 'basketball'}

def crawl_coach():
    url_template = "https://sports.dongguk.edu/page/{page_code}"
    coach_list = []
    for page_code in sports_page:
        url = url_template.format(page_code = page_code)
        response = requests.get(url)
        response.raise_for_status()  
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        prof_items = soup.select('div.prof_item')

        for item in prof_items:
            coach_data = {}
            img_tag = item.select_one('div.prof_img img')
            coach_data['img'] = 'https://sports.dongguk.edu' + img_tag['src']
            coach_data['name'] = item.select_one('div.prof_info strong').get_text(strip=True)
            coach_data['position'] = item.select_one('div.prof_info em').get_text(strip=True)
            coach_data['sports_type'] = sports_page[page_code]

            careers = {}
            for li in item.select('li'):
                # 경력 종류 추출 (선수경력 또는 지도자경력)
                career_type = li.select_one('span').get_text().strip()
                
                # 해당 경력 내용 추출
                txt_div = li.select_one('div.txt')
                
                # 경력 내용 가공
                career_list = []
                if txt_div:
                    career_entries = txt_div.get_text(separator="\n").split("\n")
                    
                    # 각 경력 항목에서 시작일, 종료일, 경력내용을 추출
                    for entry in career_entries:
                        entry = entry.strip()
                        if ':' in entry:
                            parts = entry.split('~')
                            if len(parts) == 2:
                                start_date = parts[0].strip()
                                end_date_desc = parts[1].split(":")
                                if len(end_date_desc) == 2:
                                    end_date = end_date_desc[0].strip()
                                    description = end_date_desc[1].strip()
                                    career_list.append([start_date, end_date, description])
                        else:
                            # ':'가 없을 경우 공백으로 구분
                            parts = entry.split('~')
                            if len(parts) == 2:
                                start_date = parts[0].strip()
                                rest_part = parts[1].strip()
                                end_date = rest_part.split()[0]
                                description = ' '.join(rest_part.split()[1:])
                                career_list.append([start_date, end_date, description])

                careers[career_type] = career_list

            coach_data['careers'] = careers
    
            coach_list.append(coach_data)
    
    return coach_list

load_dotenv()
uri = os.environ.get("MONGODB_URI")
client = MongoClient(uri)
db = client.get_database(os.environ.get("MONGO_DATABASE"))
collection = db['coach']

# 크롤링 후 데이터를 MongoDB에 삽입하는 함수
def insert_and_check_data():
    # 크롤링한 이벤트 데이터를 가져옵니다
    coach_list = crawl_coach()

    # 크롤링한 데이터를 MongoDB에 삽입
    result = collection.insert_many(coach_list)

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