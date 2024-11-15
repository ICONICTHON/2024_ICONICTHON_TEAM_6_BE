import json
from marshmallow import Schema, fields
from model import scheme


class CommentSchema(Schema):
    id = scheme.ObjectId()
    author = scheme.ObjectId()
    description = fields.Str()
    ct = fields.DateTime()
    mt = fields.DateTime()


class Comment(object):
    def __init__(self, json):
        self.__dict__ = json.loads(json)

    def deserialize_from_dict(self, dictionary):
        self.__dict__ = dictionary
        return self

    def deserialize_from_json(self, json):
        self.__dict__ = json.loads(json)
        return self

    def serialize_to_json(self):
        return json.dumps(self)
