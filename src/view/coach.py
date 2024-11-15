from flask import jsonify, request
from flask_restx import Namespace, Resource
from util.db import get_collection
from bson.objectid import ObjectId


coach_ns = Namespace('coach')

@coach_ns.route('/list')
class CoachList(Resource):
    def get(self):
        col = get_collection('coach')
        sports_type = request.args.get('sports_type', None)
        query = {}
        
        # sports_type이 존재하면 쿼리에 추가
        if sports_type:
            query['sports_type'] = sports_type

        res = col.find(query, {
            '_id': 1,
            'name': 1,  
            'img': 1,
            'sports_type': 1,
            'careers': 1,
            'position': 1
        })

        coach_list = list(res)

        return jsonify(coach_list)
    
@coach_ns.route('/coach/<coach_id>')
class Coach(Resource):
    def get(self, coach_id):
        col = get_collection('coach')
        res = col.find_one({'_id': ObjectId(coach_id)})

        return jsonify(res)