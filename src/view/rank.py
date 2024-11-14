from flask import jsonify, request
from flask_restx import Namespace, Resource
from bson.objectid import ObjectId
from util.db import get_collection
from pymongo import MongoClient
from dotenv import load_dotenv
import os
    

rank_ns = Namespace('rank')

@rank_ns.route('/league/<sports_type>')
class LeagueList(Resource):
    def get(self, sports_type):
        col = get_collection('rank')

        # 데이터 조회 및 필터링
        leagues = col.find(
            {'sports_type': sports_type},  # sports_type 필터링 추가
            {
                '_id': 1,  
                'year': 1,
                'league_name': 1
            }
        )

        result_dict = {}

        for league in leagues:
            year = league.get('year')
            league_name = league.get('league_name')

            if year in result_dict:
                # 이미 해당 연도의 데이터가 존재하는 경우 배열에 추가
                result_dict[year].append(league_name)
            else:
                # 새로운 연도일 경우 새로운 배열 생성
                result_dict[year] = [league_name]

        return jsonify(result_dict)

@rank_ns.route('/rank/<int:year>/<league_name>/<sports_type>')
class Rank(Resource):
    def get(self, year, league_name, sports_type):
        col = get_collection('rank')

        # MongoDB에서 year, league_name, sports_type에 맞는 데이터 찾기
        rank_data = col.find_one(
            {
                'year': year,
                'league_name': league_name,
                'sports_type': sports_type
            },
            {
                '_id': 1,  # _id 포함
                'league_record': 1
            }
        )

        # 검색된 데이터가 없는 경우 처리
        if not rank_data:
            return jsonify({"message": "No matching record found"}), 404

        # league_record를 가져와서 리스트로 변환 및 rank 기준으로 정렬
        league_record = rank_data.get('league_record', {})
        sorted_league_record = sorted(league_record.items(), key=lambda item: int(item[1]['ranking']))

        # 리스트로 변환된 데이터를 반환
        result = {
            '_id': str(rank_data['_id']),  # ObjectId를 문자열로 변환
            'sorted_league_record': sorted_league_record  # 리스트 그대로 반환
        }

        return jsonify(result)
