import json

from marshmallow import Schema, fields, validate, post_load

from model import scheme
from model.comment import CommentSchema


class Post(object):
    def __init__(self, dict):
        self.__dict__ = dict

    def deserialize_from_json(json):
        return Post(json.loads(json))

    def serialize_to_json(self):
        return json.dumps(self.__dict__)

    def serialize_to_dict(self):
        return self.__dict__


class PostSchema(Schema):
    _id = scheme.ObjectId()
    title = fields.Str()
    sports = fields.Int(validate=validate.Range(min=0, max=2))
    author = scheme.ObjectId()
    likes = fields.Int()
    description = fields.Str()
    comment = fields.List(fields.Nested(CommentSchema()))
    ct = fields.DateTime()
    mt = fields.DateTime()

    @post_load
    def new_post(self, data, **kwargs) -> Post:
        return Post(data)
