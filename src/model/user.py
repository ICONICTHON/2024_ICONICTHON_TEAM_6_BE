import json
from bson.objectid import ObjectId
from marshmallow import Schema, fields, post_load
from src.model import scheme

from src.util.db import get_collection


class UserSchema(Schema):
    _id = scheme.ObjectId()
    kakao_sub = fields.Str()
    nickname = fields.Str()
    likeposts = fields.List(scheme.ObjectId())

    @post_load
    def make_user(self, data, **kwargs):
        return User(data)


class User(object):
    def __init__(self, dict):
        self.__dict__ = dict

    def deserialize_from_json(self, json):
        self.__dict__ = json.loads(json)
        return self

    def serialize_to_json(self):
        return json.dumps(self)

    def byId(self, id: ObjectId):
        # col = get_collection('user')
        col = get_collection()
        res = col.find_one({'_id': id})
        self = UserSchema().make_user(res)
        return self

    def byIdentify(id: str):
        col = get_collection('user')
        res = col.find_one({'_id': ObjectId(id)})
        self = UserSchema().make_user(res)
        return self
