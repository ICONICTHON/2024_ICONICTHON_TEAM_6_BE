from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restx import Namespace, Resource

from model.scheme import ObjectId
from util.db import get_collection, server_info

user_ns = Namespace('user')


@user_ns.route('/me')
@user_ns.header('Authorization', 'Bearer ...')
class Me(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        col = get_collection('user')
        res = col.find_one({'id': ObjectId(user_id)})
        return jsonify(res)

    @jwt_required(fresh=True)
    def post(self):
        data = request.get_json()
        user_id = get_jwt_identity()
        col = get_collection('user')
        res = col.find_one_and_update({'_id': ObjectId(user_id)}, {'$set': {'nickname': data['nickname']}}, new=True)
        return jsonify(res)


@user_ns.route('/routes')
class Routes(Resource):
    def get(self):
        output = []
        for rule in current_app.url_map.iter_rules():
            methods = ','.join(rule.methods)
            line = "{:50s} {:20s}".format(str(rule), methods)
            output.append(line)
        return jsonify(routes=output)


@user_ns.route('/test')
class Test(Resource):
    def get(self):
        print(server_info())
        return jsonify()