import bson
from marshmallow import fields,  ValidationError, missing


class ObjectId(fields.Field):
    """bson의 field를 나타내기 위한 클래스 """

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return missing
        return str(value)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return bson.ObjectId(value)
        except ValueError as error:
            raise ValidationError("invalid ObjectId `%s`" % value) from error
