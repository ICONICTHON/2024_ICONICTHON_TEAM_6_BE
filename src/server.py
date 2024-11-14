import os
from datetime import date, datetime

from bson import Timestamp, ObjectId
from flask import Flask
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restx import Api

import config


# 커스텀 JSON encoder 생성
class UpdatedJSONProvider(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, date) or isinstance(o, datetime):
            return o.isoformat()
        elif isinstance(o, Timestamp):
            return o.as_datetime().isoformat()
        elif isinstance(o, bytes):
            return o.hex()
        elif isinstance(o, ObjectId):
            return str(o)
        return super().default(o)


authorizations = {
    'bearer_auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }, }
app = Flask(__name__)
app.json = UpdatedJSONProvider(app)
app.debug = True
api = Api(app,
          authorizations=authorizations,
          security='bearer_auth'
          )
jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    headers=['Content-Type', 'X-Requested-With', 'Authorization']
)

from view.user import user_ns
api.add_namespace(user_ns, '/api/v1/user')
from view.auth import auth_ns
api.add_namespace(auth_ns, '/api/v1/auth')
from view.post import post_ns
api.add_namespace(post_ns, '/api/v1/post')
from view.event import event_ns
api.add_namespace(event_ns, '/api/v1/event')
from view.article import article_ns
api.add_namespace(article_ns, '/api/v1/article')
from view.coach import coach_ns
api.add_namespace(coach_ns, '/api/v1/coach')
from view.static import static_ns
api.add_namespace(static_ns, '/api/v1/static')
from view.player import player_ns
api.add_namespace(player_ns, '/api/v1/player')
from view.rank import rank_ns
api.add_namespace(rank_ns, '/api/v1/rank')

if __name__ == '__main__':
    app.run(port=config.PORT, debug=config.DEBUG)
