from flask import jsonify, request
from flask_restx import Namespace, Resource
from util.db import get_collection
from bson.objectid import ObjectId

article_ns = Namespace('article')


@article_ns.route('/list')
class ArticleList(Resource):
    def get(self):
        col = get_collection('article')

        # 필요한 필드만 조회하도록 쿼리
        articles = col.find({}, {
            '_id': 1,
            'title': 1,
            'date': 1,
            'url': 1,
            'author': 1
        })

        # ObjectId를 문자열로 변환하고 article_list로 변환
        article_list = []
        for article in articles:
            article['_id'] = str(article['_id'])  # ObjectId를 문자열로 변환
            article_list.append(article)

        return jsonify(article_list)

    @article_ns.route('/recent')
    class ArticleList(Resource):
        def get(self):
            col = get_collection('article')

            # 필요한 필드만 조회하도록 쿼리
            articles = col.find({}, {
                '_id': 1,
                'title': 1,
                'date': 1,
                'summary': 1,
                'url': 1
            }).sort("date", -1).limit(3)

            # ObjectId를 문자열로 변환하고 article_list로 변환
            article_list = []
            for article in articles:
                article['_id'] = str(article['_id'])  # ObjectId를 문자열로 변환
                article_list.append(article)

            return jsonify(article_list)


@article_ns.route('/description/<article_id>')
class Description(Resource):
    def get(self, article_id):
        col = get_collection('article')
        res = col.find_one(
            {'_id': ObjectId(article_id)},
            {'_id': 1, 'description': 1}
        )

        return jsonify(res)


@article_ns.route('/summary/<article_id>')
class Summary(Resource):
    def get(self, article_id):
        col = get_collection('article')
        res = col.find_one(
            {'_id': ObjectId(article_id)},
            {'_id': 1, 'summary': 1}
        )

        return jsonify(res)
