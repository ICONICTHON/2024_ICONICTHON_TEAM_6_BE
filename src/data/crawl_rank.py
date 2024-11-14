import requests, re, os, pprint
from bs4 import BeautifulSoup
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv
from bson.objectid import ObjectId


e_code_list = {
    6: "basketball", 
    34: "baseball", 
    45: "soccer"
    }

basketball_year_lcode = {
    2024: (197, ),
    2023: (165, ),
    2022: (149, 158),
    2021: (116, 120, 122, 129),
    2020: (49, 96, 97),
    2019: (15, 35),
    2018: (65, 80)
}

basketball_year_tcode = {

    2024: 1233,
    2023: 1056,
    2022: 958,
    2021: 821,
    2020: 458,
    2019: 200,
    2018: 8
}

baseball_year_lcode = {
    2024: (206, ),
    2023: (183, 193),
    2022: (151, 161),
    2021: (111, 125),
    2020: (51, 92),
    2019: (10, 33),
    2018: (83, 84, 86)
}

baseball_year_tcode = {

    2024: 1308,
    2023: 1187,
    2022: 987,
    2021: 775,
    2020: 481,
    2019: 172,
    2018: 28
}

soccer_year_lcode = {
    2024: (212, ),
    2023: (167, ),
    2022: (139, ),
    2021: (101, ),
    2020: (58, 98),
    2019: (22, 33),
    2018: (71, 79)
}

soccer_year_tcode = {

    2024: 1369,
    2023: 1078,
    2022: 866,
    2021: 699,
    2020: 602,
    2019: 227,
    2018: 76
}

def crawl_rank():
    rank_result = []
    for e_code in e_code_list:
        if e_code == 6:
            year_to_lcode = basketball_year_lcode
            record_keys = [
                        'ranking', 'nog', 'win_rate', 'wins', 'lose',
                        'score', 'as', 'rb', 'st', 'bl', 
                        'two', 'three', 'ft'
                        ]
        elif e_code == 34:
            year_to_lcode = baseball_year_lcode
            record_keys = [
                        'ranking', 'nog', 'win_point', 'wins', 'draw',
                        'lose', 'win_rate', 'oba', 'sa'
                        ]
        elif e_code == 45:
            year_to_lcode = soccer_year_lcode 
            record_keys = [
                        'ranking', 'nog', 'win_point', 'wins', 'draw', 
                        'lose', 'score', 'loss', 'margin', 'as', 'yellow', 'red'
                        ]
        # URL 템플릿
        url_template = "https://www.kusf.or.kr/league/league_ranking.html?e_code={e_code}&ptype=&l_year={l_year}&l_mon=&l_code={l_code}"

        for l_year, lcode_list in year_to_lcode.items():
            for l_code in lcode_list:
                url = url_template.format(e_code=e_code, l_year=l_year, l_code=l_code)
                print(f"Fetching URL: {url}")
                try:
                    # 페이지 요청
                    response = requests.get(url)
                    response.raise_for_status()  # 응답 상태 코드가 200이 아니면 HTTPError 발생
                    response.encoding = 'utf-8'
                    # HTML 소스 파싱
                    soup = BeautifulSoup(response.text, 'html.parser')
                    rank_data = {}
                    rank_data['year'] = l_year
                    rank_data['sports_type'] = e_code_list[e_code]
                    rank_data['league_name'] =  soup.select_one('div.kind2 option[selected]').text

                    team_names = [th.text.strip() for th in soup.select('tbody#LeagueStatsTable_tit th.tleft')]
                    team_records = []
                    for tr in soup.select('tbody#LeagueStatsTable_table tr'):
                        record_values = [td.text.strip() for td in tr.find_all('td')]
                        record_dict = dict(zip(record_keys, record_values))
                        team_records.append(record_dict)
                    # 학교 이름을 key로, 각 기록들을 담은 딕셔너리를 value로 하는 딕셔너리 생성
                    team_data = dict(zip(team_names, team_records))
                    rank_data['league_record'] = team_data
                    rank_result.append(rank_data)
                    print(f"Successfully fetched data for e_code={e_code}, l_year={l_year}, l_code={l_code}")
                    

                except requests.exceptions.HTTPError as http_err:
                    print(f"HTTP error occurred: {http_err} - e_code={e_code},l_year={l_year}, l_code={l_code}")
                
                except Exception as err:
                    print(f"Other error occurred: {err} - e_code={e_code}, l_year={l_year}, l_code={l_code}")
    
    return rank_result

load_dotenv()
uri = os.environ.get("MONGODB_URI")
client = MongoClient(uri)
db = client.get_database(os.environ.get("MONGO_DATABASE"))
collection = db['rank']

# 크롤링 후 데이터를 MongoDB에 삽입하는 함수
def insert_and_check_data():
    # 크롤링한 이벤트 데이터를 가져옵니다
    rank_list = crawl_rank()
    # 크롤링한 데이터를 MongoDB에 삽입
    result = collection.insert_many(rank_list)

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