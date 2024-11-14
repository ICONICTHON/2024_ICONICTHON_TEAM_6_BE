import datetime

from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restx import Namespace, fields, Resource
from marshmallow import utils, ValidationError

from model.post import PostSchema
from model.scheme import ObjectId
from model.user import User
from util.db import get_collection

post_ns = Namespace('post')

comment_res = post_ns.model('comment_res', {
    "author": fields.String(example="woiefjownf..."),
    "ct": fields.String(example="2024-08-15T00:00:00.000000"),
    "mt": fields.String(example="2024-08-15T00:00:00.000000"),
    "description": fields.String(example="그래서 말인데요. 변경된 댓글이 뭐라고요? 저도 잘 모르겠는데..."),

})

post_res = post_ns.model('post_res', {
    "_id": fields.String(example="aoifejowefn..."),
    "author": fields.String(example="woiefjownf..."),
    "comment": fields.List(fields.Nested(comment_res)),
    "ct": fields.String(example="2024-08-15T00:00:00.000000"),
    "mt": fields.String(example="2024-08-15T00:00:00.000000"),
    "description": fields.String(example="그래서 말인데요. 변경된 글이 뭐라고요? 저도 잘 모르겠는데..."),
    "likes": fields.Integer(example=100),
    "sports": fields.Integer(example=2),
    "title": fields.String(example="이거슨 변경된 글의 새 제목입니다"),
}
                         )


def isNotAuthor(user_id: str, post_id: str):
    user = User.byIdentify(user_id)
    colp = get_collection('post')
    post = colp.find_one({"_id": ObjectId(post_id)})
    if user._id == post.author:
        return False
    return True


def isNotCommentAuthor(user_id: str, post_id: str, comment_index: int):
    user = User.byIdentify(user_id)
    colp = get_collection('post')
    post = colp.find_one({'_id': ObjectId(post_id)})
    if user._id == post['comment'][comment_index]['author']:
        return False
    return True


@post_ns.route('/post')
class Post(Resource):
    @post_ns.response(200, 'Success', post_ns.model('post_list_res', {
        'posts': fields.List(fields.Nested(post_res, description="Post 목록"))
    }))
    def get(self):
        '''커뮤니티 글 목록 불러오기'''
        col = get_collection('post')
        res = col.find().sort("ct", -1).limit(100)
        return jsonify(({"posts": list(res)}))


@post_ns.expect(post_ns.model('new_post_req', {
    'title': fields.String(description='title', required=True, example='이것은 글의 제목입니다.'),
    'sports': fields.Integer(description="sports code", reuired=True, example=0),
    'description': fields.String(description="description", reuired=True, example="그래서 말인데요. 글이 뭐라고요? 저도 잘 모르겠는데...")
}))
@post_ns.response(200, 'Success', post_ns.model('new_post_res', {
    'post_id': fields.String(description="생성된 post id", example="adfjwf3r93...")
}))
@jwt_required()
def post(self):
    '''커뮤니티 글 작성'''
    user = User.byIdentify(get_jwt_identity())
    data = request.get_json()
    data_server = {
        "author": user._id,
        "likes": 0,
        "comment": [],
        "ct": utils.isoformat(datetime.datetime.now()),
        "mt": utils.isoformat(datetime.datetime.now()),
    }
    try:
        new_post = PostSchema().new_post({**data, **data_server}, partial=True)
    except ValidationError as e:
        print(e.messages)
        return {"message": "ValidationError"}

    col = get_collection('post')
    res = col.insert_one(new_post.serialize_to_dict())
    return jsonify({"post_id": res.inserted_id})


@post_ns.route('/hot')
class PostHot(Resource):
    def get(self):
        '''인기글'''
        col = get_collection('post')
        res = col.find().sort("likes", -1).limit(100)
        return jsonify({"posts": list(res)})


@post_ns.route('/post/<post_id>')
class PostWithId(Resource):
    def get(self, post_id):
        '''글 상세 조회'''
        col = get_collection('post')
        res = col.find_one({'_id': ObjectId(post_id)})
        colu = get_collection('user')
        res['author'] = colu.find_one({'_id': ObjectId(res['author'])})['nickname']
        for i, v in enumerate(res['comment']):
            res['comment'][i]['author'] = colu.find_one({'_id': ObjectId(v['author]'])})['nickname']
        return jsonify(res)


@post_ns.expect(post_ns.model('edit_post_req', {
    'title': fields.String(description="title", reuired=True, example="이것은 변경된 글의 제목입니다."),
    'sports': fields.Integer(description="sports code", reuired=True, example=0),
    'description': fields.String(description="description", reuired=True,
                                 example="그래서 말인데요. 변경된 글이 뭐라고요? 저도 잘 모르겠는데..."),
}))
@post_ns.response(200, 'Success', post_res)
@jwt_required()
def patch(self, post_id):
    '''커뮤니티 글 수정'''
    if isNotAuthor(get_jwt_identity(), post_id):
        return jsonify({"message": 'You are not the author of this post!'}), 403
    data = request.get_json()
    data_server = {
        "mt": utils.isoformat(datetime.datetime.now()),
    }
    try:
        new_post = PostSchema().new_post({**data, **data_server}, partial=True)
    except ValidationError as e:
        print(e.messages)
        return {"message": "ValidationError"}

    col = get_collection('post')
    res = col.find_one_and_update(
        {'_id': ObjectId(post_id)},
        {'$set': new_post.serialize_to_dict()},
        new=True
    )
    return jsonify(res)


@post_ns.route('/sports/<int:sports>')
class PostWithScode(Resource):
    @post_ns.response(200, 'Success', post_ns.model('post_list_res', {
        'posts': fields.List(fields.Nested(post_res, description="Post들의 목록"))
    }))
    def get(self, sports):
        '''스포츠 별 글 목록'''
        col = get_collection('post')
        res = col.find({'sports': sports}).sort("ct", -1).limit(100)
        return jsonify({"posts": list(res)})


@post_ns.route('/like/<post_id>')
class LikePost(Resource):
    @jwt_required()
    def get(self, post_id):
        '''게시글 좋아요'''
        colp = get_collection('post')
        colu = get_collection('user')
        colu.update_one(
            {'_id': ObjectId(get_jwt_identity())},
            {'$push': {'likeposts': ObjectId(post_id)}}
        )
        colp.update_one({'_id': ObjectId(post_id)}, {'$inc': {'likes': 1}})
        return jsonify({'message': 'Success'})


@post_ns.route('/unlike/<post_id>')
class UnlikePost(Resource):
    @jwt_required()
    def get(self, post_id):
        '''좋아요 취소'''
        colp = get_collection('post')
        colu = get_collection('user')
        colu.update_one(
            {'_id': ObjectId(get_jwt_identity())},
            {'$pull': {'likeposts': ObjectId(post_id)}}
        )
        colp.update_one({'_id': ObjectId(post_id)}, {'$inc': {'likes': -1}})
        return jsonify({'message': 'Success'})


@post_ns.route('/comment/<post_id>')
class Comment(Resource):
    @post_ns.expect(post_ns.model('new_comment', {
        'description': fields.String(description='description', required=True,
                                     example="그래서 말인데요. 댓글이 뭐라고요? 저도 잘 모르겠는데...")
    }))
    @post_ns.response(200, 'Success', post_res)
    @jwt_required()
    def post(self, post_id):
        '''댓글 작성'''
        data = request.get_json()
        col = get_collection('post')
        user = User.byIdentify(get_jwt_identity())
        res = col.find_one_and_update({'_id': ObjectId(post_id)}, {'$push': {'comment': {
            'description': data['description'],
            'author': ObjectId(get_jwt_identity()),
            'ct': utils.isoformat(datetime.datetime.now()),
            'mt': utils.isoformat(datetime.datetime.now()),
        }}}, new=True)
        res['author'] = User.byIdentify(res['author']).nickname
        for i, v in enumerate(res['comment']):
            res['comment'][i]['author'] = User.byIdentify(v['author']).nickname
        return jsonify(res)


@post_ns.route('/comment/<post_id>/<int:comment_index>')
class CommentWithIndex(Resource):
    @jwt_required()
    def patch(self, post_id, comment_index):
        '''댓글 수정'''
        if isNotCommentAuthor(get_jwt_identity(), post_id, comment_index):
            return jsonify({"message": 'You are not the author of this post!'}), 403
        data = request.get_json()
        col = get_collection('post')
        res = col.find_one_and_update(
            {'_id': ObjectId(post_id)},
            {'$set': {f"comment.{comment_index}.description": data['description'],
                      f"comment.{comment_index}.mt": utils.isoformat(datetime.datetime.now())}
             }, new=True)
        return jsonify(res)

    @jwt_required()
    def delete(self, post_id, comment_index):
        '''댓글 삭제'''
        if isNotCommentAuthor(get_jwt_identity(), post_id, comment_index):
            return jsonify({'message': 'You are not the author of this post!'}), 403
        data = request.get_json()
        col = get_collection('post')
        res = col.find_one_and_update(
            {'_id': ObjectId(post_id)},
            {'$pop': {'comment': comment_index, }}, new=True)
        return jsonify({'message': 'Success!'})
