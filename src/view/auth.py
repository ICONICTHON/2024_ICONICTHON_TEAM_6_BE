import os

import requests
from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flask_restx import Namespace, Resource, fields

from util.db import get_collection

auth_ns = Namespace('auth')


@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(auth_ns.model('login_req', {
        'accessToken': fields.String(description='accessToken', required=True, example='adfjwf3r93...')
    }))
    @auth_ns.response(200, 'Success', auth_ns.model('login_res', {
        'accessToken': fields.String(description='accessToken', required=True, example='adfjwf3r93...'),
        'refreshToken': fields.String(description='refreshToken', required=True, example='adfjwf3r93...')
    }))
    def post(self):
        data = request.get_json()
        res = requests.get(
            f"{os.environ.get('KAPI_HOST')}//v1/oidc/userinfo",
            headers={'Authorization': 'Bearer ' + data['accessToken']})
        if res.status_code == 200:
            res_data = res.json()
            sub = res_data['sub']
            nickname = res_data['nickname']
            ## DB에 있는 회원인지 확인 후 없으면 회원가입, 있으면 로그인 토큰 발급
            col = get_collection('user')
            user = col.find_one({'kakao_sub': sub, })
            user_id: str
            if user is None:
                inserted_user = col.insert_one({"nickname": nickname, "kakao_sub": sub, })
                user_id = inserted_user.inserted_id
            else:
                user_id = user['_id']
            access_token = create_access_token(identity=str(user_id), fresh=True)
            refresh_token = create_refresh_token(identity=str(user_id))
            return jsonify({"accessToken": access_token, "refreshToken": refresh_token})
        else:
            return {"error": "Internal Server Error"}


@auth_ns.route('/testLogin')
class TestLogin(Resource):
    def post(self):
        user_id = request.get_json()['user_id']
        access_token = create_access_token(identity=str(user_id), fresh=True)
        refresh_token = create_refresh_token(identity=str(user_id))
        return jsonify({"accessToken": access_token, "refreshToken": refresh_token})


@auth_ns.route('/logout')
class Logout(Resource):
    @jwt_required()
    def post(self):
        return jsonify({})


@auth_ns.route('/protected')
class Protected(Resource):
    @jwt_required(fresh=True)
    def get(self):
        return jsonify({"You are": get_jwt_identity()})


@auth_ns.route('/refresh')
class Refresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        identity = get_jwt_identity()
        access_token = create_access_token(identity=identity, fresh=True)
        return jsonify({"accessToken": access_token})
