from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
import sys
import os
import json

#The Steam API key is mandatory (obtain through a Steam account)
APIKEY = os.environ.get('STEAM_APIKEY')
if not APIKEY:
    print("Specify the 'STEAM_APIKEY' environment variable.")
    sys.exit(1)

BASE_URL = 'http://api.steampowered.com'
DOTA2_ID = 'IDOTA2Match_570'

def build_endpoint(endpoint):
    '''
    Builds a conforming URL for this API, game ID, and method
    '''

    return '/'.join([BASE_URL, endpoint])

def open_endpoint(url, params={}):
    '''
    Send a request to the specified endpoint with query params.
    Decodes the JSON reply and returns the decoded object.
    '''

    query = dict(params, key=APIKEY)
    req = "{}?{}".format(url, urlencode(query))
    data = urlopen(req).read().decode()
        
    return json.loads(data)

def get_live_league_games():
    '''
    Calls GetLiveLeagueGames endpoint which details a list of
    "league" games in progress. 
    '''

    url = build_endpoint('/'.join([DOTA2_ID, 'GetLiveLeagueGames', 'v1']))
    return open_endpoint(url)

