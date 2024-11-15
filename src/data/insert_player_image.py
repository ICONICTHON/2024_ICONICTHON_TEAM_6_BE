import os
from dotenv import load_dotenv
from pymongo import MongoClient

# 환경 변수 로드
load_dotenv()

uri = os.environ.get("MONGODB_URI")
client = MongoClient(uri)
db = client.get_database(os.environ.get("MONGO_DATABASE"))
collection = db['player']

# 업로드된 이미지 경로 설정
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(CURRENT_DIR, '../../static/player_img')

# 이미지 파일 처리 및 업데이트
for f in os.listdir(UPLOAD_FOLDER):
    if os.path.isfile(os.path.join(UPLOAD_FOLDER, f)):
        name = os.path.splitext(f)[0]  # 파일명에서 확장자 제거한 이름
        url = f'https://nanoby.duckdns.org/api/v1/static/player_img/{f}'  # URL 생성

        # 'name' 필드가 일치하는 문서의 'img' 필드를 새로운 URL로 업데이트
        existing = collection.find_one({'name': name})
        if existing:
            if existing:
                collection.update_one({'name': name}, {'$set': {'img': url}})
        