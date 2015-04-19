'''
Thin wrapper to make requests to Steam's web API.
Prerequisites:
    Set an appropriate STEAM_APIKEY environment variable.
    Requires Tornado framework (running IOLoop) for async HTTP requests
'''
import logging
import sys
import os
import json
from urllib.parse import urlencode

from tornado.httpclient import AsyncHTTPClient
from tornado import gen

logger = logging.getLogger('dotaware')
#The Steam API key is mandatory (obtain through a Steam account)
APIKEY = os.environ.get('STEAM_APIKEY')
if not APIKEY:
    print("Specify the 'STEAM_APIKEY' environment variable.")
    sys.exit(1)
logger.info("STEAM_APIKEY={}".format(APIKEY))

BASE_URL = 'http://api.steampowered.com'
DOTA2_ID = 'IDOTA2Match_570'
CLIENT = AsyncHTTPClient()

def build_endpoint(endpoint):
    '''
    Builds a conforming URL for this API, game ID, and method
    '''
    req = '{}/{}'.format(BASE_URL, endpoint)
    return req

@gen.coroutine
def async_request(url, params={}):
    '''
    Asynchronously make a request.
    Decodes the result and returns it as a dict
    '''
    query = dict(params, key=APIKEY)
    req = '{}?{}'.format(url, urlencode(query))
    logger.debug(req)
    res = yield CLIENT.fetch(req)
    #TODO: handle exceptions
    return json.loads(res.body.decode())
    

@gen.coroutine
def get_live_league_games():
    '''
    Calls GetLiveLeagueGames endpoint which details a list of
    "league" games in progress. 
    Returns a Future containing the response body.
    '''
    logger.debug('')
    url = build_endpoint('/'.join([DOTA2_ID, 'GetLiveLeagueGames', 'v1']))
    data = yield async_request(url)
    #logger.debug(data) #TODO: remove
    return data

