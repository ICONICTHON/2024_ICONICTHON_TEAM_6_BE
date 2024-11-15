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

def crawl_basketball_player():
    e_code = 6
    # URL 템플릿
    url_template = "https://www.kusf.or.kr/league/league_ranking_player.html?e_code={e_code}&ptype=&l_year={l_year}&l_code={l_code}&t_code={t_code}&srch_word="
    player_data = []
    id_list = []
    for l_year, t_code in basketball_year_tcode.items():
        for l_code in basketball_year_lcode[l_year]:
            url = url_template.format(e_code=e_code, l_year=l_year, l_code=l_code, t_code=t_code)                          
            print(f"Fetching URL: {url}")
            
            try:    
                # 페이지 요청
                response = requests.get(url)
                response.raise_for_status()  # 응답 상태 코드가 200이 아니면 HTTPError 발생
                response.encoding = 'utf-8'
                # HTML 소스 파싱
                soup = BeautifulSoup(response.text, 'html.parser')
                a_tags = soup.select('tbody#LeagueStatsTable_tit a')
                
                # p_code 추출
                for a in a_tags:
                    href = a.get('href')    
                    player_url = f"https://www.kusf.or.kr{href}"
                    try:
                        player_record = {}
                        response = requests.get(player_url)
                        response.raise_for_status()  # 응답 상태 코드가 200이 아니면 HTTPError 발생
                        response.encoding = 'utf-8'
                        # HTML 소스 파싱
                        soup = BeautifulSoup(response.text, 'html.parser')  
                        player_record['name'] = soup.select_one('div.playerBasic.mb60 td.person p').text.strip()
                        player_record['birthday'] = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(1) td:nth-of-type(1)').text.strip()
                        player_record['no'] =  int(soup.select_one('div.playerBasic.mb60 td.person strong').text.strip().replace('#', '').strip())
                        player_record['position'] = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(3) td:nth-of-type(1)').text.strip()
                        player_record['grade'] = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(3) td:nth-of-type(2)').text.strip()
                        player_record['id'] =  f"{player_record['name']} {player_record['birthday']}"
                        height = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(2) td:nth-of-type(1)').text.strip()
                        weight = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(2) td:nth-of-type(2)').text.strip()
                        player_record['physical_info'] = {'height': height, 'weight': weight}
                        player_record['highschool'] = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(4) td:nth-of-type(1)').text.strip()
                        player_record['sports_type'] = 'basketball'
                        img_link = soup.select_one('div.playerBasic.mb60 td.img img')['src']
                        if img_link:
                            img = 'https://kusf.or.kr' + img_link
                        else:
                            img = ""

                        player_record['img'] = img

                        if l_year == 2024:
                            player_record['now'] = 1
                        else:
                            player_record['now'] = 0

                        years_divs = soup.select('div.playerCase_Scroll')
                        years_div = years_divs[2]
                        record_key = ['nog', 'score', 'min', 'two', 'three', 'ft', 'rb', 'as', 'st', 'bl', 'foul']
                        l_years = [td.text.strip() for td in years_div.select('.tbls1.rankCase.playerCase_Scroll_tit tbody td')]
                        # 리그 기록 추출
                        yearly_record = []
                        for tr in soup.select('div.playerCase_Scroll_sub.playerScroll3 tbody tr'):
                            record_dict = dict(zip(record_key, [td.text.strip() for td in tr.find_all('td')]))
                            yearly_record.append(record_dict)
                        league_record = dict(zip(l_years, yearly_record))
                        player_record['league_record'] = league_record

                        years_div = years_divs[3]
                        t_years = [td.text.strip() for td in years_div.select('.tbls1.rankCase.playerCase_Scroll_tit tbody td')]
                        # 토너먼트 기록 추출
                        yearly_record = []
                        for tr in soup.select('.playerCase_Scroll_sub.playerScroll4 tbody tr'):
                            record_dict = dict(zip(record_key, [td.text.strip() for td in tr.find_all('td')]))
                            yearly_record.append(record_dict)
                        tournament_record = dict(zip(t_years, yearly_record))
                        player_record['tournament_record'] = tournament_record
                        # 중복제거
                        if player_record['id'] not in id_list:
                            id_list.append(player_record['id'])
                            player_data.append(player_record)
                        
                    except requests.exceptions.HTTPError as http_err:
                        print(f"HTTP error occurred: {http_err} - player_url={player_url}")
                    except Exception as err:
                        print(f"Other error occurred: {err} - player_url={player_url}") 
                print(f"Successfully fetched data for e_code={e_code}, l_year={l_year}, l_code={l_code}, t_code={t_code}")

            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error occurred: {http_err} - e_code={e_code},l_year={l_year},l_code={l_code}, t_code={t_code}")
        
            except Exception as err:
                print(f"Other error occurred: {err} - e_code={e_code}, l_year={l_year}, l_code={l_code}, t_code={t_code}")
            
    return player_data


def crawl_baseball_player():
    e_code = 34
    # URL 템플릿
    url_template = "https://www.kusf.or.kr/league/league_ranking_player.html?e_code={e_code}&ptype={ptype}&l_year={l_year}&l_code={l_code}&t_code={t_code}&srch_word="
    player_data = []
    id_list = []
    hitter_key = ['nog', 'ba', 'appearance', 'hit', 'hit2', 'hit3', 'hr', 'score,' 'steal', 'walks', 'k', 'obp', 'slg', 'ops']
    pitcher_key = ['nog', 'era', 'inning', 'wins', 'lose', 'k', 'hits', 'hr', 'er,' 'walks', 'dead', 'whip']
    for l_year, t_code in baseball_year_tcode.items():
        for l_code in baseball_year_lcode[l_year]:
            # tuta 확인을 위한 리스트
            hitter_list = []
            hitter_url = url_template.format(e_code=e_code, ptype = "", l_year=l_year, l_code=l_code, t_code=t_code)
            pitcher_url = url_template.format(e_code=e_code, ptype = "p", l_year=l_year, l_code=l_code, t_code=t_code)                          
            print(f"Fetching URL: {hitter_url}")
            
            try:    
                # 페이지 요청
                response = requests.get(hitter_url)
                response.raise_for_status()  # 응답 상태 코드가 200이 아니면 HTTPError 발생
                response.encoding = 'utf-8'
                # HTML 소스 파싱
                soup = BeautifulSoup(response.text, 'html.parser')
                a_tags = soup.select('tbody#LeagueStatsTable_tit a')
                
                # p_code 추출
                for a in a_tags:
                    href = a.get('href')    
                    player_url = f"https://www.kusf.or.kr{href}"
                    try:
                        player_record = {}
                        response = requests.get(player_url)
                        response.raise_for_status()  # 응답 상태 코드가 200이 아니면 HTTPError 발생
                        response.encoding = 'utf-8'
                        # HTML 소스 파싱
                        soup = BeautifulSoup(response.text, 'html.parser')  
                        player_record['name'] = soup.select_one('div.playerBasic.mb60 td.person p').text.strip()
                        player_record['birthday'] = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(1) td:nth-of-type(1)').text.strip()
                        player_record['no'] =  int(soup.select_one('div.playerBasic.mb60 td.person strong').text.strip().replace('#', '').strip())
                        player_record['position'] = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(3) td:nth-of-type(1)').text.strip()
                        player_record['grade'] = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(3) td:nth-of-type(2)').text.strip()
                        player_record['id'] =  f"{player_record['name']} {player_record['birthday']}"
                        height = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(2) td:nth-of-type(1)').text.strip()
                        weight = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(2) td:nth-of-type(2)').text.strip()
                        player_record['physical_info'] = {'height': height, 'weight': weight}
                        player_record['highschool'] = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(4) td:nth-of-type(1)').text.strip()
                        player_record['sports_type'] = 'baseball'
                        img_link = soup.select_one('div.playerBasic.mb60 td.img img')['src']
                        if img_link:
                            img = 'https://kusf.or.kr' + img_link
                        else:
                            img = ""

                        player_record['img'] = img

                        if l_year == 2024:
                            player_record['now'] = 1
                        else:
                            player_record['now'] = 0

                        player_record['tuta'] =  0

                        years_divs = soup.select('div.playerCase_Scroll')
                        years_div = years_divs[2]
                        l_years = [td.text.strip() for td in years_div.select('.tbls1.rankCase.playerCase_Scroll_tit tbody td')]
                        # 리그 기록 추출
                        yearly_record = []
                        for tr in soup.select('div.playerCase_Scroll_sub.playerScroll3 tbody tr'):
                            record_dict = dict(zip(hitter_key, [td.text.strip() for td in tr.find_all('td')]))
                            yearly_record.append(record_dict)
                        league_record = dict(zip(l_years, yearly_record))
                        player_record['league__hitter_record'] = league_record

                        years_div = years_divs[3]
                        t_years = [td.text.strip() for td in years_div.select('.tbls1.rankCase.playerCase_Scroll_tit tbody td')]
                        # 토너먼트 기록 추출
                        yearly_record = []
                        for tr in soup.select('.playerCase_Scroll_sub.playerScroll4 tbody tr'):
                            record_dict = dict(zip(hitter_key, [td.text.strip() for td in tr.find_all('td')]))
                            yearly_record.append(record_dict)
                        tournament_record = dict(zip(t_years, yearly_record))
                        player_record['tournament_hitter_record'] = tournament_record

                        # 중복제거
                        if player_record['id'] not in id_list:
                            id_list.append(player_record['id'])
                            player_data.append(player_record)
                            hitter_list.append(player_record['id'])
                                    
                    except requests.exceptions.HTTPError as http_err:
                        print(f"HTTP error occurred: {http_err} - player_url={player_url}")
                    except Exception as err:
                        print(f"Other error occurred: {err} - player_url={player_url}") 
                print(f"Successfully fetched data for e_code={e_code}, l_year={l_year}, l_code={l_code}, t_code={t_code}")

            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error occurred: {http_err} - e_code={e_code},l_year={l_year},l_code={l_code}, t_code={t_code}")
        
            except Exception as err:
                print(f"Other error occurred: {err} - e_code={e_code}, l_year={l_year}, l_code={l_code}, t_code={t_code}")

            print(f"Fetching URL: {pitcher_url}")
            try:    
                # 페이지 요청
                response = requests.get(pitcher_url)
                response.raise_for_status()  # 응답 상태 코드가 200이 아니면 HTTPError 발생
                response.encoding = 'utf-8'
                # HTML 소스 파싱
                soup = BeautifulSoup(response.text, 'html.parser')
                a_tags = soup.select('tbody#LeagueStatsTable_tit a')
                
                # p_code 추출
                for a in a_tags:
                    href = a.get('href')    
                    player_url = f"https://www.kusf.or.kr{href}"
                    try:
                        player_record = {}
                        response = requests.get(player_url)
                        response.raise_for_status()  # 응답 상태 코드가 200이 아니면 HTTPError 발생
                        response.encoding = 'utf-8'
                        # HTML 소스 파싱
                        soup = BeautifulSoup(response.text, 'html.parser')  
                        player_record['name'] = soup.select_one('div.playerBasic.mb60 td.person p').text.strip()
                        player_record['birthday'] = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(1) td:nth-of-type(1)').text.strip()
                        player_record['no'] =  int(soup.select_one('div.playerBasic.mb60 td.person strong').text.strip().replace('#', '').strip())
                        player_record['position'] = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(3) td:nth-of-type(1)').text.strip()
                        player_record['grade'] = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(3) td:nth-of-type(2)').text.strip()
                        player_record['id'] =  f"{player_record['name']} {player_record['birthday']}"
                        height = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(2) td:nth-of-type(1)').text.strip()
                        weight = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(2) td:nth-of-type(2)').text.strip()
                        player_record['physical_info'] = {'height': height, 'weight': weight}
                        player_record['highschool'] = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(4) td:nth-of-type(1)').text.strip()
                        player_record['sports_type'] = 'baseball'
                        img_link = soup.select_one('div.playerBasic.mb60 td.img img')['src']
                        if img_link:
                            img = 'https://kusf.or.kr' + img_link
                        else:
                            img = ""
                        player_record['img'] = img

                        if l_year == 2024:
                            player_record['now'] = 1
                        else:
                            player_record['now'] = 0

                        player_record['tuta'] = 1
                        
                        years_divs = soup.select('div.playerCase_Scroll')
                        years_div = years_divs[6]
                        l_years = [td.text.strip() for td in years_div.select('.tbls1.rankCase.playerCase_Scroll_tit tbody td')]
                        # 리그 기록 추출
                        yearly_record = []
                        for tr in soup.select('div.playerCase_Scroll_sub.playerScroll23 tbody tr'):
                            record_dict = dict(zip(pitcher_key, [td.text.strip() for td in tr.find_all('td')]))
                            yearly_record.append(record_dict)
                        league_record = dict(zip(l_years, yearly_record))
                        player_record['league_pitcher_record'] = league_record

                        years_div = years_divs[7]
                        t_years = [td.text.strip() for td in years_div.select('.tbls1.rankCase.playerCase_Scroll_tit tbody td')]
                        # 토너먼트 기록 추출
                        yearly_record = []
                        for tr in soup.select('.playerCase_Scroll_sub.playerScroll24 tbody tr'):
                            record_dict = dict(zip(pitcher_key, [td.text.strip() for td in tr.find_all('td')]))
                            yearly_record.append(record_dict)
                        tournament_record = dict(zip(t_years, yearly_record))
                        player_record['tournament_pitcher_record'] = tournament_record

                        # 중복제거
                        if player_record['id'] not in id_list:
                            id_list.append(player_record['id'])
                            player_data.append(player_record)
                        
                                    
                    except requests.exceptions.HTTPError as http_err:
                        print(f"HTTP error occurred: {http_err} - player_url={player_url}")
                    except Exception as err:
                        print(f"Other error occurred: {err} - player_url={player_url}") 
                print(f"Successfully fetched data for e_code={e_code}, l_year={l_year}, l_code={l_code}, t_code={t_code}")

            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error occurred: {http_err} - e_code={e_code},l_year={l_year},l_code={l_code}, t_code={t_code}")
        
            except Exception as err:
                print(f"Other error occurred: {err} - e_code={e_code}, l_year={l_year}, l_code={l_code}, t_code={t_code}")
    
    return player_data


def crawl_soccer_player():
    e_code = 45
    # URL 템플릿
    url_template = "https://www.kusf.or.kr/league/league_ranking_player.html?e_code={e_code}&ptype=&l_year={l_year}&l_code={l_code}&t_code={t_code}&srch_word="
    player_data = []
    id_list = []
    for l_year, t_code in soccer_year_tcode.items():
        for l_code in soccer_year_lcode[l_year]:
            url = url_template.format(e_code=e_code, l_year=l_year, l_code=l_code, t_code=t_code)                          
            print(f"Fetching URL: {url}")
            
            try:    
                # 페이지 요청
                response = requests.get(url)
                response.raise_for_status()  # 응답 상태 코드가 200이 아니면 HTTPError 발생
                response.encoding = 'utf-8'
                # HTML 소스 파싱
                soup = BeautifulSoup(response.text, 'html.parser')
                a_tags = soup.select('tbody#LeagueStatsTable_tit a')
                
                # p_code 추출
                for a in a_tags:
                    href = a.get('href')    
                    player_url = f"https://www.kusf.or.kr{href}"
                    try:
                        player_record = {}
                        response = requests.get(player_url)
                        response.raise_for_status()  # 응답 상태 코드가 200이 아니면 HTTPError 발생
                        response.encoding = 'utf-8'
                        # HTML 소스 파싱
                        soup = BeautifulSoup(response.text, 'html.parser')  
                        player_record['name'] = soup.select_one('div.playerBasic.mb60 td.person p').text.strip()
                        player_record['birthday'] = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(1) td:nth-of-type(1)').text.strip()
                        player_record['no'] =  soup.select_one('div.playerBasic.mb60 td.person strong').text.strip().replace('#', '').strip()
                        player_record['position'] = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(3) td:nth-of-type(1)').text.strip()
                        player_record['grade'] = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(3) td:nth-of-type(2)').text.strip()
                        player_record['id'] =  f"{player_record['name']} {player_record['birthday']}"
                        height = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(2) td:nth-of-type(1)').text.strip()
                        weight = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(2) td:nth-of-type(2)').text.strip()
                        player_record['physical_info'] = {'height': height, 'weight': weight}
                        player_record['highschool'] = soup.select_one('div.playerBasic.mb60 div.right tr:nth-of-type(4) td:nth-of-type(1)').text.strip()
                        player_record['sports_type'] = 'soccer'
                        img_link = soup.select_one('div.playerBasic.mb60 td.img img')['src']

                        if img_link:
                            img = 'https://kusf.or.kr' + img_link
                        else:
                            img = ""

                        player_record['img'] = img

                        if l_year == 2024:
                            player_record['now'] = 1
                        else:
                            player_record['now'] = 0

                        years_divs = soup.select('div.playerCase_Scroll')
                        years_div = years_divs[2]
                        record_key = ['nog', 'score', 'as', 'yellow', 'red']
                        l_years = [td.text.strip() for td in years_div.select('.tbls1.rankCase.playerCase_Scroll_tit tbody td')]
                        # 리그 기록 추출
                        yearly_record = []
                        for tr in soup.select('div.playerCase_Scroll_sub.playerScroll3 tbody tr'):
                            record_dict = dict(zip(record_key, [td.text.strip() for td in tr.find_all('td')]))
                            yearly_record.append(record_dict)
                        league_record = dict(zip(l_years, yearly_record))
                        player_record['league_record'] = league_record

                        years_div = years_divs[3]
                        t_years = [td.text.strip() for td in years_div.select('.tbls1.rankCase.playerCase_Scroll_tit tbody td')]
                        # 토너먼트 기록 추출
                        yearly_record = []
                        for tr in soup.select('.playerCase_Scroll_sub.playerScroll4 tbody tr'):
                            record_dict = dict(zip(record_key, [td.text.strip() for td in tr.find_all('td')]))
                            yearly_record.append(record_dict)
                        tournament_record = dict(zip(t_years, yearly_record))
                        player_record['tournament_record'] = tournament_record
                        # 중복제거
                        if player_record['id'] not in id_list:
                            id_list.append(player_record['id'])
                            player_data.append(player_record)
                        
                        
                    except requests.exceptions.HTTPError as http_err:
                        print(f"HTTP error occurred: {http_err} - player_url={player_url}")
                    except Exception as err:
                        print(f"Other error occurred: {err} - player_url={player_url}") 
                print(f"Successfully fetched data for e_code={e_code}, l_year={l_year}, l_code={l_code}, t_code={t_code}")

            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error occurred: {http_err} - e_code={e_code},l_year={l_year},l_code={l_code}, t_code={t_code}")
        
            except Exception as err:
                print(f"Other error occurred: {err} - e_code={e_code}, l_year={l_year}, l_code={l_code}, t_code={t_code}")
    
    return player_data

load_dotenv()
uri = os.environ.get("MONGODB_URI")
client = MongoClient(uri)
db = client.get_database(os.environ.get("MONGO_DATABASE"))
collection = db['player']

# 크롤링 후 데이터를 MongoDB에 삽입하는 함수
def insert_and_check_data():
    # 크롤링한 이벤트 데이터를 가져옵니다
    basketball_player_list = crawl_basketball_player()
    baseball_player_list = crawl_baseball_player()
    soccer_player_list = crawl_soccer_player()
    player_list = basketball_player_list + baseball_player_list + soccer_player_list

    # 크롤링한 데이터를 MongoDB에 삽입
    result = collection.insert_many(player_list)

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