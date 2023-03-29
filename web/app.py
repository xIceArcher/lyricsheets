import json

from ..api import api

from flask import Flask
from flask.wrappers import Response
from dataclass_wizard import asdict


config_file_path = './config.json'

with open(config_file_path) as f:
    cfg = json.load(f)
    redis_cfg = cfg['redis']

songAPI = api.CachedSongServer(
    cfg['google_credentials'], cfg['spreadsheet_id'],
    redis_cfg['host'], redis_cfg['port'], redis_cfg['db']
)
app = Flask(__name__)

@app.route("/songs/<title>")
def get_song_handler(title: str):
    return Response(songAPI.get_song(title).to_json(), content_type='application/json')
