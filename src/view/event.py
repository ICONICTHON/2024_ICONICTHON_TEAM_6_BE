from datetime import datetime

from bson import ObjectId
from flask import jsonify, request
from flask_restx import Namespace, Resource

from util.db import get_collection

event_ns = Namespace('event')


@event_ns.route('/list')
class EventList(Resource):
    def get(self):
        col = get_collection('events')
        university_col = get_collection('university')
        sports_type = request.args.get('sports_type', None)
        query = {}
        
        # sports_type이 존재하면 쿼리에 추가
        if sports_type:
            query['sports_type'] = sports_type

        res = col.find(query, {
            '_id': 1,
            'event_time': 1,
            'm_code': 1,
            'sports_type': 1,
            'location': 1,
            'university': 1,
            'league': 1,
            'score': 1
        })
        events = list(res)
        for event in events:
            if "university" in event and event["university"]:
                university_ids = [ObjectId(id) for id in event["university"]]
                universities = list(university_col.find(
                    {"_id": {"$in": university_ids}},
                    {"_id": 0, "team": 1, "img": 1}
                ))

                # `team`과 `img` 리스트 생성
                event["teams"] = [u["team"] for u in universities]
                event["img"] = [u["img"] for u in universities]
                del event["university"]  

        if events:
            return jsonify(events)
        
        else:
            return jsonify({"message": "No events found"}), 404
    
@event_ns.route('/detail/<event_id>')
class Detail(Resource):
    def get(self, event_id):
        col = get_collection('events')
        res = col.find_one(
            {'_id': ObjectId(event_id)},
            {'_id': 1, 'team_record': 1}
        )
        if res:
            return jsonify(res)
        else:
            return jsonify({"message": "Event not found"}), 404


@event_ns.route('/simple/<event_id>')
class Simple(Resource):
    def get(self, event_id):
        col = get_collection('events')
        university_col = get_collection('university')
        res = col.find_one(
            {'_id': ObjectId(event_id)},
            {'_id': 1,
             'event_time': 1,
             'sports_type': 1,
             'location': 1,
             'university':1,
             'league': 1,
             'score': 1
             }
        )
        
        if "university" in res and res["university"]:
            university_ids = [ObjectId(id) for id in res["university"]]
            universities = list(university_col.find(
                {"_id": {"$in": university_ids}},
                {"_id": 0, "team": 1, "img": 1}
            ))

            # `team`과 `img` 리스트 생성
            res["teams"] = [u["team"] for u in universities]
            res["img"] = [u["img"] for u in universities]
            del res["university"]  

        if res:
            return jsonify(res)
        else:
            return jsonify({"message": "Event not found"}), 404

          
@event_ns.route('/month/<int:year>/<int:month>')
class Month(Resource):
    def get(self, year, month):
        col = get_collection('events')
        university_col = get_collection('university')  
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        # 기본 쿼리 조건
        query = {
            'event_time': {
                '$gte': start_date,
                '$lt': end_date
            }
        }

        # 쿼리 파라미터로 sports_type 받기
        sports_type = request.args.get('sports_type', None)

        # sports_type이 존재하면 쿼리에 추가
        if sports_type:
            query['sports_type'] = sports_type
        

        field = {
            '_id': 1,
            'event_time': 1,
            'm_code': 1,
            'sports_type': 1,
            'location': 1,
            'university': 1,
            'league': 1,
            'score': 1
        }

        # MongoDB에서 쿼리 실행
        events = col.find(query, field)
        
        event_list = []
        for event in events:
            # university 필드에 저장된 ID 리스트를 사용하여 teams와 img 조회
            if "university" in event and event["university"]:
                university_ids = [ObjectId(id) for id in event["university"]]
                universities = list(university_col.find(
                    {"_id": {"$in": university_ids}},
                    {"_id": 0, "team": 1, "img": 1}
                ))

                # 조회한 university 데이터를 teams와 img 리스트로 변환
                event["teams"] = [u["team"] for u in universities]
                event["img"] = [u["img"] for u in universities]

            # 더 이상 필요 없는 university 필드는 제거
            event.pop("university", None)
            
            # ObjectId를 문자열로 변환
            event['_id'] = str(event['_id']) 
            event_list.append(event)

        return jsonify(event_list)
    
@event_ns.route('/day/<int:year>/<int:month>/<int:day>')
class Day(Resource):
    def get(self, year, month, day):
        col = get_collection('events')
        university_col = get_collection('university')
        # 시작 시간과 종료 시간 설정 (해당 날짜의 00:00:00 ~ 23:59:59)
        start_date = datetime(year, month, day, 0, 0, 0)
        end_date = datetime(year, month, day, 23, 59, 59)

        # 기본 쿼리 조건 (해당 날짜 범위 내의 이벤트)
        query = {
            'event_time': {
                '$gte': start_date,
                '$lt': end_date
            }
        }

        # 쿼리 파라미터로 sports_type 받기
        sports_type = request.args.get('sports_type', None)

        # sports_type이 존재하면 쿼리에 추가
        if sports_type:
            query['sports_type'] = sports_type
        
        field = {
            '_id': 1,
            'event_time': 1,
            'm_code': 1,
            'sports_type': 1,
            'location': 1,
            'university': 1,
            'league': 1,
            'score': 1
        }

        # MongoDB에서 쿼리 실행
        events = col.find(query, field)
        
        event_list = []
        for event in events:
            # university 필드에 저장된 ID 리스트를 사용하여 teams와 img 조회
            if "university" in event and event["university"]:
                university_ids = [ObjectId(id) for id in event["university"]]
                universities = list(university_col.find(
                    {"_id": {"$in": university_ids}},
                    {"_id": 0, "team": 1, "img": 1}
                ))

                # 조회한 university 데이터를 teams와 img 리스트로 변환
                event["teams"] = [u["team"] for u in universities]
                event["img"] = [u["img"] for u in universities]

            # 더 이상 필요 없는 university 필드는 제거
            event.pop("university", None)
            
            # ObjectId를 문자열로 변환
            event['_id'] = str(event['_id']) 
            event_list.append(event)

        return jsonify(event_list)
