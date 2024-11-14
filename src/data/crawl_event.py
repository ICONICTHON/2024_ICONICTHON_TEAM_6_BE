import requests, re, os, pprint
from bs4 import BeautifulSoup
from pymongo import MongoClient, ASCENDING
from datetime import datetime, timezone
from dotenv import load_dotenv
from bson.objectid import ObjectId



load_dotenv()
uri = os.environ.get("MONGODB_URI")
client = MongoClient(uri)
db = client.get_database(os.environ.get("MONGO_DATABASE"))
collection = db['events']
collection2 = db['university']

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
# 대학 테이블에 존재하는지 확인하고 없다면 추가
def add_university(team_name, img_url):
    # 기존 문서에서 team_name을 찾기
    existing = collection2.find_one({"team": team_name})

    if existing:
        # team_name이 존재하면 해당 _id를 반환
        return existing["_id"]
    else:
        # team_name이 없으면 새 문서를 삽입하고 생성된 _id를 반환
        result = collection2.insert_one({
            "team": team_name,
            "img": img_url
        })
        return result.inserted_id
        
# 크롤링 함수
def crawl_event():
    event_result = []
    for e_code in e_code_list:    
        if e_code == 6:
            year_to_tcode = basketball_year_tcode
        elif e_code == 34:
            year_to_tcode = baseball_year_tcode
        elif e_code == 45:
            year_to_tcode = soccer_year_tcode    
        
        # URL 템플릿
        url_template = "https://www.kusf.or.kr/league/league_schedule.html?e_code={e_code}&ptype=&l_year={l_year}&l_mon=&l_code=&t_code={t_code}"
        
        # l_year 반복
        for l_year, t_code in year_to_tcode.items():
            # URL 생성
            url = url_template.format(e_code=e_code, l_year=l_year, t_code=t_code)
            print(f"Fetching URL: {url}")
            
            try:
                # 페이지 요청
                response = requests.get(url)
                response.raise_for_status()  # 응답 상태 코드가 200이 아니면 HTTPError 발생
                response.encoding = 'utf-8'
                # HTML 소스 파싱
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 모든 경기 일정을 포함하는 li 태그들을 찾기
                li_tags = soup.select('div.sls1 ul li')

                for li in li_tags:
                    col1_span = li.find('span', class_ = 'col1')
                    if col1_span:
                        league = col1_span.text.strip()
                    
                    left_team = li.find('span', class_= 'left').find('em').text.strip()
                    right_team = li.find('span', class_= 'right').find('em').text.strip()

                    left_img = 'https://www.kusf.or.kr' + li.find('span', class_= 'left').find('img')['src']
                    right_img = 'https://www.kusf.or.kr' + li.find('span', class_= 'right').find('img')['src']
                    
                    left_university = add_university(left_team, left_img)
                    right_university = add_university(right_team, right_img)
                    university = [left_university, right_university]
                    
                    # col2 클래스를 가진 div 태그에서 날짜와 시간을 포함하는 텍스트를 추출
                    col2_div = li.find('div', class_='col2')
                    if col2_div:
                        # 날짜와 시간 정보를 추출
                        date_text = col2_div.contents[0].strip()  # 첫 번째 텍스트 노드
                        time_location_text = col2_div.find('span').text.strip()  # span 태그 안의 텍스트
                        # start_time과 location 분리
                        start_time = f"{date_text} {time_location_text.split()[0]}"
                        event_time = convert_to_datetime(start_time, l_year)
                        location = ' '.join(time_location_text.split()[1:])    
                    # socre 정보 추출
                    score_text = li.find('strong').find('span').find('em').text.strip()
                    if score_text == 'VS':
                        score = ['','']
                    elif score_text == "우천취소":
                        score = "우천취소"
                    else:
                        score = [s.strip() for s in score_text.split(':')]
                    # m_code 정보 추출, 경기기록 주소를 구분, 중복 제거를 위한 정보
                    m_code = ''
                    col4_span = li.find('span', class_='col4')
                    if col4_span:
                        a_tag = col4_span.find('a')
                        if a_tag and 'href' in a_tag.attrs:
                            m_code = a_tag['href'].split('=')[-1]
                            result_url = f"https://www.kusf.or.kr/league/{a_tag['href']}"
                    
                            try:
                                if(e_code == 6): #basketball 기록일 때
                                    team_record, player_record = crawl_basketball_result(result_url)
                                
                                elif(e_code == 34):
                                    team_record, player_record = crawl_baseball_result(result_url)

                                elif(e_code == 45):
                                    team_record, player_record = crawl_soccer_result(result_url)
                            
                            except requests.exceptions.HTTPError as http_err:
                                print(f"HTTP error occurred: {http_err} - result_url={result_url}")
                            except Exception as err:
                                print(f"Other error occurred: {err} - result_url={result_url}")
                
                    
                    event_data = {
                            'event_time': event_time, 
                            'm_code': m_code, 'sports_type': e_code_list[e_code], 
                            'location': location,
                            'university': university,
                            'league': league, 
                            'score': score, 
                            'team_record': team_record, 
                            'player_record': player_record,
                            'inserted_at': datetime.now(timezone.utc)
                            }
                    event_result.append(event_data)

                print(f"Successfully fetched data for e_code={e_code}, l_year={l_year}, t_code={t_code}")
            
            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error occurred: {http_err} - e_code={e_code},l_year={l_year}, t_code={t_code}")
            
            except Exception as err:
                print(f"Other error occurred: {err} - e_code={e_code}, l_year={l_year}, t_code={t_code}, m_code={m_code}")
    
    return event_result


def crawl_basketball_result(url):
    response = requests.get(url)
    response.raise_for_status()
    response.encoding = 'utf-8'

    soup = BeautifulSoup(response.text, 'html.parser')

    # 각 tr 태그 찾기
    tr_tags = soup.select('div.rankCase_Scroll_sub.rec_team tbody tr')

    # 각 tr 태그 내의 td 태그의 텍스트를 배열로 변환
    team_record = []
    team_keys = ['q1', 'q2', 'q3', 'q4', 'rb', 'as', 'steal', 'bl', 'foul', 'two', 'tree', 'free']
    for tr in tr_tags:
        td_values = [td.text.strip() for td in tr.find_all('td')]
        td_dict = dict(zip(team_keys, td_values))
        team_record.append(td_dict)

    #선수 고유 p_code 추출
    home_pcodes = []
    href_tags = soup.select('div.tab-con.tabData2 tbody a')
    for tag in href_tags:
        href = tag['href']
        p_code = href.split('p_code=')[1].split('&')[0]
        home_pcodes.append(p_code)
    
    away_pcodes = []
    href_tags = soup.select('div.tab-con.tabData3 tbody a')
    for tag in href_tags:
        href = tag['href']
        p_code = href.split('p_code=')[1].split('&')[0]
        away_pcodes.append(p_code)

    
    player_keys = ['score', 'time', 'two_per', 'three_per', 'freethrow_per', 'rb', 'as', 'steal', 'bl', 'foul']
    home_values = []
    away_values = []
    
    home_tags = soup.select('div.rankCase_Scroll_sub.rec_player1 tbody tr')
    away_tags = soup.select('div.rankCase_Scroll_sub.rec_player2 tbody tr')

    for tr in home_tags:
        player_values = [td.text.strip() for td in tr.find_all('td')]
        home_dict = dict(zip(player_keys, player_values))
        home_values.append(home_dict)
    
    home_player = dict(zip(home_pcodes, home_values))

    for tr in away_tags:
        player_values = [td.text.strip() for td in tr.find_all('td')]
        away_dict = dict(zip(player_keys, player_values))
        away_values.append(away_dict)
    
    away_player = dict(zip(away_pcodes, away_values))

    player_record = [home_player, away_player]

    return team_record, player_record

def crawl_baseball_result(url):
    response = requests.get(url)
    response.raise_for_status()
    response.encoding = 'utf-8'

    soup = BeautifulSoup(response.text, 'html.parser')

    # 야구 경기기록 tr 태그 찾기
    game_tags = soup.select('div.rankCase_Scroll_sub.rec_boxscore tbody tr')
    game_record = []
    game_keys = ['i1', 'i2', 'i3', 'i4', 'i5', 'i6', 'i7', 'i8', 'i9', 'runs', 'hits', 'errors' , 'base_on_balls']
    
    for tr in game_tags:
        td_values = [td.text.strip() for td in tr.find_all('td')]
        td_dict = dict(zip(game_keys, td_values))
        game_record.append(td_dict)

    # 야구 팀기록 tr 태그 찾기
    team_tags = soup.select('div.rankCase_Scroll_sub.rec_team tbody tr')
    team_record = []
    team_keys = ['score', 'hit', 'hit2', 'hit3', 'hr', 'steal', 'k', 'error', 'obp', 'slg']

    for tr in team_tags:
        td_values = [td.text.strip() for td in tr.find_all('td')]
        td_dict = dict(zip(team_keys, td_values))
        team_record.append(td_dict)
    
    # 경기기록과 팀기록을 합친다.
    for i in range(len(team_record)):
        team_record[i]['score_detail'] = game_record[i]

    # 홈팀 선수 p_code 추출
    home_tbody = soup.select('div.tab-con.tabData2 tbody')
    home_pcodes = {}
    hitter_pcodes = []
    pitcher_pcodes = []

    hitter_href_tags = home_tbody[0].find_all("a")
    for tag in hitter_href_tags:
        href = tag['href']
        p_code = href.split('p_code=')[1].split('&')[0]
        hitter_pcodes.append(p_code)
    home_pcodes['hitter'] = hitter_pcodes

    pitcher_href_tags = home_tbody[2].find_all("a")
    for tag in pitcher_href_tags:
        href = tag['href']
        p_code = href.split('p_code=')[1].split('&')[0]
        pitcher_pcodes.append(p_code)
    home_pcodes['pitcher'] = pitcher_pcodes
    
    # 원정팀 선수 p_code 추출
    away_tbody = soup.select('div.tab-con.tabData3 tbody')
    away_pcodes = {}
    hitter_pcodes = []
    pitcher_pcodes = []

    hitter_href_tags = away_tbody[0].find_all("a")
    for tag in hitter_href_tags:
        href = tag['href']
        p_code = href.split('p_code=')[1].split('&')[0]
        hitter_pcodes.append(p_code)
    away_pcodes['hitter'] = hitter_pcodes

    pitcher_href_tags = away_tbody[2].find_all("a")
    for tag in pitcher_href_tags:
        href = tag['href']
        p_code = href.split('p_code=')[1].split('&')[0]
        pitcher_pcodes.append(p_code)
    away_pcodes['pitcher'] = pitcher_pcodes
    
    # 타자와 투수의 기록 키 설정
    hitter_keys = ['타석', '타수', '안타', '타점', '득점', '2타', '3타', '홈런', '도루', '희타', '희비', '4구', '사구', '삼진']
    pitcher_keys = ['선발', '승패', '이닝', '타자', '투구수', '타수', '안타', '홈런', '희타', '희비', '4구', '사구', '삼진', '폭투', '보크', '실점', '자책점']
    
    home_hitter_tags = soup.select('div.rankCase_Scroll_sub.rec_player1 tbody tr')
    home_pitcher_tags = soup.select('div.rankCase_Scroll_sub.rec_player2 tbody tr')
    away_hitter_tags = soup.select('div.rankCase_Scroll_sub.rec_player3 tbody tr')
    away_pitcher_tags = soup.select('div.rankCase_Scroll_sub.rec_player4 tbody tr')

    home_pitcher_values = []
    home_hitter_values = []

    for tr in home_hitter_tags:
        hitter_values = [td.text.strip() for td in tr.find_all('td')]
        home_dict = dict(zip(hitter_keys, hitter_values))
        home_hitter_values.append(home_dict)
    
    for tr in home_pitcher_tags:
        pitcher_values = [td.text.strip() for td in tr.find_all('td')]
        home_dict = dict(zip(pitcher_keys, pitcher_values))
        home_pitcher_values.append(home_dict)

    position = ['hitter', 'pitcher']
    home_hitter = dict(zip(home_pcodes['hitter'], home_hitter_values))
    home_pitcher = dict(zip(home_pcodes['pitcher'], home_pitcher_values))
    home_record = dict(zip(position, [home_hitter, home_pitcher]))

    away_pitcher_values = []
    away_hitter_values = []

    for tr in away_hitter_tags:
        hitter_values = [td.text.strip() for td in tr.find_all('td')]
        away_dict = dict(zip(hitter_keys, hitter_values))
        away_hitter_values.append(away_dict)
    
    for tr in away_pitcher_tags:
        pitcher_values = [td.text.strip() for td in tr.find_all('td')]
        away_dict = dict(zip(pitcher_keys, pitcher_values))
        away_pitcher_values.append(away_dict)

    away_hitter = dict(zip(away_pcodes['hitter'], away_hitter_values))
    away_pitcher = dict(zip(away_pcodes['pitcher'], away_pitcher_values))
    away_record = dict(zip(position, [away_hitter, away_pitcher]))
    player_record = [home_record, away_record]

    return team_record, player_record

def crawl_soccer_result(url):
    response = requests.get(url)
    response.raise_for_status()
    response.encoding = 'utf-8'

    soup = BeautifulSoup(response.text, 'html.parser')

    # 각 tr 태그 찾기
    tr_tags = soup.select('div.rankCase_Scroll_sub.rec_team tbody tr')

    # 각 tr 태그 내의 td 태그의 텍스트를 배열로 변환
    team_record = []
    team_keys = ['first', 'second', 'as', 'yellow', 'red']
    for tr in tr_tags:
        td_values = [td.text.strip() for td in tr.find_all('td')]
        td_dict = dict(zip(team_keys, td_values))
        team_record.append(td_dict)

    #선수 고유 p_code 추출
    home_pcodes = []
    href_tags = soup.select('div.tab-con.tabData2 tbody a')
    for tag in href_tags:
        href = tag['href']
        p_code = href.split('p_code=')[1].split('&')[0]
        home_pcodes.append(p_code)
    
    away_pcodes = []
    href_tags = soup.select('div.tab-con.tabData3 tbody a')
    for tag in href_tags:
        href = tag['href']
        p_code = href.split('p_code=')[1].split('&')[0]
        away_pcodes.append(p_code)

    
    player_keys = ['score', 'as', 'yellow', 'red']
    home_values = []
    away_values = []
    
    home_tags = soup.select('div.rankCase_Scroll_sub.rec_player1 tbody tr')
    away_tags = soup.select('div.rankCase_Scroll_sub.rec_player2 tbody tr')

    for tr in home_tags:
        player_values = [td.text.strip() for td in tr.find_all('td')]
        home_dict = dict(zip(player_keys, player_values))
        home_values.append(home_dict)
    
    home_player = dict(zip(home_pcodes, home_values))

    for tr in away_tags:
        player_values = [td.text.strip() for td in tr.find_all('td')]
        away_dict = dict(zip(player_keys, player_values))
        away_values.append(away_dict)
    
    away_player = dict(zip(away_pcodes, away_values))

    player_record = [home_player, away_player]

    return team_record, player_record

def convert_to_datetime(start_time, l_year):
    # '11.04(일) 16:00' 형태의 문자열을 파싱
    date_part, time_part = start_time.split()  # '11.04(일)'과 '16:00'으로 나눔

    # 날짜 부분에서 월과 일을 추출
    date_part = re.sub(r'\(.*?\)', '', date_part).strip()  # '11.04'로 변환
    month, day = date_part.split('.')  # '11', '04'로 분리
    month = int(month)
    day = int(day)

    # 시간 부분에서 시와 분을 추출
    hour, minute = time_part.split(':')  # '16', '00'으로 분리
    hour = int(hour)
    minute = int(minute)

    # l_year와 함께 datetime 객체로 변환
    return datetime(l_year, month, day, hour, minute)

def additional_data():
    data_list = [{
                            'event_time': datetime(2024, 4, 12, 9, 0, 0), 
                            'sports_type': 34, 
                            'location': '홍천 야구장',
                            'university': [collection2.find_one({"team": '동국대'})["_id"]
                                           , collection2.find_one({"team": '한양대'})["_id"]],
                            'league': '2024 대학야구 U리그', 
                            'score': ['6', '0'], 
                            'inserted_at': datetime.now(timezone.utc)
                            },
                            {
                            'event_time': datetime(2024, 4, 16, 11, 30, 0), 
                            'sports_type': 34, 
                            'location': '홍천 야구장',
                            'university': [collection2.find_one({"team": '동국대'})["_id"]
                                           , collection2.find_one({"team": '디지털서울문화예술대'})["_id"]],
                            'league': '2024 대학야구 U리그', 
                            'score': ['4', '8'], 
                            'inserted_at': datetime.now(timezone.utc)
                            },
                            {
                            'event_time': datetime(2024, 4, 26, 11, 30, 0), 
                            'sports_type': 34, 
                            'location': '홍천 야구장',
                            'university': [collection2.find_one({"team": '동국대'})["_id"]
                                           , collection2.find_one({"team": '인하대'})["_id"]],
                            'league': '2024 대학야구 U리그', 
                            'score': ['4', '8'], 
                            'inserted_at': datetime.now(timezone.utc)
                            },
                            {
                            'event_time': datetime(2024, 7, 17, 17, 0, 0), 
                            'sports_type': 45, 
                            'location': '상주 실내체육관(신관)',
                            'university': [collection2.find_one({"team": '동국대'})["_id"]
                                           , collection2.find_one({"team": '명지대'})["_id"]],
                            'league': '2024 제40회 MBC배', 
                            'score': ['89', '65'], 
                            'inserted_at': datetime.now(timezone.utc)
                            },
                            {
                            'event_time': datetime(2024, 7, 19, 15, 0, 0), 
                            'sports_type': 45, 
                            'location': '상주 실내체육관(신관)',
                            'university': [collection2.find_one({"team": '동국대'})["_id"]
                                           , collection2.find_one({"team": '건국대'})["_id"]],
                            'league': '2024 제40회 MBC배', 
                            'score': ['56', '63'], 
                            'inserted_at': datetime.now(timezone.utc)
                            },
                            {
                            'event_time': datetime(2024, 7, 21, 15, 0, 0), 
                            'sports_type': 45, 
                            'location': '상주 실내체육관(신관)',
                            'university': [collection2.find_one({"team": '동국대'})["_id"]
                                           , collection2.find_one({"team": '연세대'})["_id"]],
                            'league': '2024 제40회 MBC배', 
                            'score': ['50', '76'], 
                            'inserted_at': datetime.now(timezone.utc)
                            },
                            {
                            'event_time': datetime(2024, 8, 18, 16, 0, 0), 
                            'sports_type': 6, 
                            'location': '고원2구장',
                            'university': [collection2.find_one({"team": '동국대'})["_id"]
                                           , collection2.find_one({"team": '조선대'})["_id"]],
                            'league': '2024 추계 대학축구연맹전', 
                            'score': ['1', '3'], 
                            'inserted_at': datetime.now(timezone.utc)
                            }]
    result = collection.insert_many(data_list)

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

                            

# 크롤링 후 데이터를 MongoDB에 삽입하는 함수
def insert_and_check_data():
    # 크롤링한 이벤트 데이터를 가져옵니다
    event_list = crawl_event()

    # 크롤링한 데이터를 MongoDB에 삽입
    result = collection.insert_many(event_list)

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
    additional_data()