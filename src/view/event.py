from datetime import datetime

from flask import jsonify, request
from flask_restx import Namespace, Resource

from model.scheme import ObjectId
from util.db import get_collection

event_ns = Namespace('event')


@event_ns.route('/list')
class EventList(Resource):
    def get(self):
        col = get_collection('events')
        sports_type = request.args.get('sports_type', None)
        query = {}

        if sports_type:
            query['sports_type'] = sports_type

        res = col.find(query, {
            '_id': 1,
            'event_time': 1,
            'm_code': 1,
            'sports_type': 1,
            'location': 1,
            'img': 1,
            'teams': 1,
            'league': 1,
            'score': 1
        })
        events = list(res)

        if events:
            return jsonify(events)
        else:
            return jsonify({'message': 'No events found'}), 404


@event_ns.route('/detail/<event_id>')
class Detail(Resource):
    def get(self, event_id):
        col = get_collection('events')
        res = col.find_one(
            {'_id': ObjectId(event_id)},
            {'_id': 1, 'team_record': 1}
        )
        if res:
            return jsonify(res)
        else:
            return jsonify({"message": "Event not found"}), 404


@event_ns.route('/delete/<event_id>')
class Simple(Resource):
    def get(self, event_id):
        col = get_collection('events')
        res = col.find_one(
            {'_id': ObjectId(event_id)},
            {'_id': 1,
             'event_time': 1,
             'sports_type': 1,
             'location': 1,
             'img': 1,
             'teams': 1,
             'league': 1,
             'score': 1
             }
        )
        if res:
            return jsonify(res)
        else:
            return jsonify({"message": "Event not found"}), 404


@event_ns.route('/month/<int:year>/<int:month>')
class Month(Resource):
    def get(self, year, month):
        col = get_collection('events')
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        query = {
            'event_time': {
                '$gte': start_date,
                '$lt': end_date
            }
        }
        sports_type = request.args.get('sports_type', None)
        query = {}
        if sports_type:
            query['sports_type'] = sports_type
        res = col.find(query, {
            '_id': 1,
            'event_time': 1,
            'm_code': 1,
            'sports_type': 1,
            'location': 1,
            'img': 1,
            'teams': 1,
            'league': 1,
            'score': 1
        })
        events = list(res)
        if events:
            return jsonify(events)
        else:
            return jsonify({'message': 'No events found'}), 404


@event_ns.route('/detail/<event_id>')
class Detail(Resource):
    def get(self, event_id):
        col = get_collection('events')
        res = col.find_one(
            {'_id': ObjectId(event_id)},
            {'_id': 1, 'team_record': 1}
        )
        if res:
            return jsonify(res)
        else:
            return jsonify({"message": "Event not found"}), 404


@event_ns.route('/simple/<event_id>')
class Simple(Resource):
    def get(self, event_id):
        col = get_collection('events')
        res = col.find_one(
            {'_id': ObjectId(event_id)},
            {'_id': 1,
             'event_time': 1,
             'sports_type': 1,
             'location': 1,
             'img': 1,
             'teams': 1,
             'league': 1,
             'score': 1
             }
        )
        if res:
            return jsonify(res)
        else:
            return jsonify({"message": "Event not found"}), 404


@event_ns.route('/month/<int:year>/<int:month>')
class Month(Resource):
    def get(self, year, month):
        col = get_collection('events')
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        query = {
            'event_time': {
                '$gte': start_date,
                '$lt': end_date
            }
        }
        sports_type = request.args.get('sports_type', None)
        if sports_type:
            query['sports_type'] = sports_type
        field = {
            '_id': 1,
            'event_time': 1,
            'm_code': 1,
            'sports_type': 1,
            'location': 1,
            'img': 1,
            'teams': 1,
            'league': 1,
            'score': 1
        }
        events = col.find(query, field)
        event_list = []
        for event in events:
            event['_id'] = str(event['_id'])
            event_list.append(event)
        return jsonify(event_list)


@event_ns.route('/day/<int:year>/<int:month>/<int:day>')
class Day(Resource):
    def get(self, year, month, day):
        col = get_collection('events')
        start_date = datetime(year, month, day, 0, 0, 0)
        end_date = datetime(year, month, day, 23, 59, 59)
        query = {
            'event_time': {
                '$gte': start_date,
                '$lt': end_date
            }
        }
        sports_type = request.args.get('sports_type', None)
        if sports_type:
            query['sports_type'] = sports_type
        field = {
            '_id': 1,
            'event_time': 1,
            'm_code': 1,
            'sports_type': 1,
            'location': 1,
            'img': 1,
            'teams': 1,
            'league': 1,
            'score': 1
        }
        events = col.find(query, field)
        event_list = []
        for event in events:
            event['_id'] = str(event['_id'])
            event_list.append(event)
        return jsonify(event_list)
