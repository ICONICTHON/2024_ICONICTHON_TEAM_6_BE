from flask import jsonify, request
from flask_restx import Namespace, Resource
from util.db import get_collection
from bson.objectid import ObjectId

player_ns = Namespace('player')

@player_ns.route('/search/<query>')
class Search(Resource):
    def get(self, query):
        col = get_collection('player')
        
        if len(query) < 2:
            return jsonify([])
        
        regex_query = {'name': {'$regex': f'^{query}', '$options': 'i'}}
        
        # 검색된 선수 데이터 찾기
        players = col.find(regex_query, {
            '_id': 1,
            'name': 1,
            'birthday': 1,
            'no': 1,
            'position': 1,
            'physical_info': 1,
            'highschool': 1,
            'sports_type': 1,
            'img': 1
        })

        player_list = []
        for player in players:
            player['_id'] = str(player['_id'])  # ObjectId를 문자열로 변환
            player_list.append(player)

        return jsonify(player_list)


    
@player_ns.route('/profile/<player_id>')
class Profile(Resource):
    def get(self, player_id):
        col = get_collection('player')
        res = col.find_one({'_id': ObjectId(player_id)}, 
                           { '_id': 1, 'name': 1, 'birthday': 1, 'no': 1, 'position': 1, 'physical_info': 1, 'highschool': 1, 'grade': 1, 'tuta':1, 'sports_type': 1, 'img': 1})
        if not res:
            return jsonify({'message': 'Player not found'}), 404
        
        return jsonify(res)
    

@player_ns.route('/list')
class PlayerList(Resource):
    def get(self):
        col = get_collection('player')

        # 기본 쿼리 조건: now 필드가 1인 데이터만 가져옴
        query = {'now': 1}
        
        # 쿼리 파라미터로 sports_type 받기
        sports_type = request.args.get('sports_type', None)

        # sports_type이 존재하면 쿼리에 추가
        if sports_type:
            query['sports_type'] = sports_type

        # 기본 필드 설정
        fields = {
            '_id': 1, 
            'name': 1,
            'no': 1,
            'position': 1,
            'sports_type': 1, 
            'img': 1
        }
        
        # sports_type이 baseball일 경우 'tuta' 필드도 추가
        if sports_type == 'baseball':
            fields['tuta'] = 1

        # MongoDB에서 now가 1인 선수들만 가져오고, 필터 조건이 있으면 추가 적용
        players = col.find(query, fields)
        
        player_list = []
        for player in players:
            player['_id'] = str(player['_id'])  # ObjectId를 문자열로 변환
            player_list.append(player)
        
        return jsonify(player_list)



@player_ns.route('/record/<player_id>')
class Record(Resource):
    def get(self, player_id):
        col = get_collection('player')
        res = col.find_one({'_id': ObjectId(player_id)}, 
                           {'_id': 1, 'league_record': 1})
        # 검색된 선수가 없는 경우 처리
        if not res:
            return jsonify({'message': 'Player not found'}), 404
        return jsonify(res)