import json

from ..api import api

from flask import Flask
from flask.wrappers import Response

config_file_path = './config.json'

with open(config_file_path) as f:
    cfg = json.load(f)
    redis_cfg = cfg['redis']

songAPI = api.SongAPI(
    cfg['google_credentials'], cfg['spreadsheet_id'],
    redis_cfg['host'], redis_cfg['port'], redis_cfg['db']
)
app = Flask(__name__)

@app.route("songs/<title>")
def get_song_handler(title: str):
    return Response(json.dumps(songAPI.get_song(title)), content_type='application/json')
