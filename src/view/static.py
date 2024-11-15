from flask import send_from_directory, jsonify, make_response
from flask_restx import Namespace, Resource
import os
# Namespace 설정
static_ns = Namespace('static')

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(CURRENT_DIR, '../../static/player_img')

@static_ns.route('/player_img/<img_name>')
class PlayerImg(Resource):
    def get(self, img_name):
        try:
            response = send_from_directory(UPLOAD_FOLDER, img_name)
            return make_response(response)

        except FileNotFoundError:
            # Return a JSON error for missing files
            return {"error": "File not found"}, 404

        except Exception as e:
            # Return a JSON error for unexpected issues
            return {"error": str(e)}, 500
