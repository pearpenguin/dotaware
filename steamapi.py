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

#The Steam API key is mandatory (obtain through a Steam account)
APIKEY = os.environ.get('STEAM_APIKEY')
if not APIKEY:
    print("Specify the 'STEAM_APIKEY' environment variable.")
    sys.exit(1)
logging.info("STEAM_APIKEY={}".format(APIKEY))

BASE_URL = 'http://api.steampowered.com'
STEAM_REMOTE_STORAGE = 'ISteamRemoteStorage'
DOTA2_ID = '570'
DOTA2_MATCH = 'IDOTA2Match_' + DOTA2_ID
DOTA2_ECON = 'IEconDOTA2_' + DOTA2_ID
CLIENT = AsyncHTTPClient()

def build_endpoint(endpoint):
    '''
    Builds a conforming URL for this API, game ID, and method
    '''
    req = '{}/{}'.format(BASE_URL, endpoint)
    return req

@gen.coroutine
def request(url, params={}):
    '''
    Asynchronously make a request to any URL to get arbitrary resources
    using AsyncHTTPClient.
    '''
    req = '{}?{}'.format(url, urlencode(params))
    logging.debug(req)
    res = yield CLIENT.fetch(req)
    return res.body

@gen.coroutine
def async_request(url, params={}):
    '''
    Asynchronously make a request to Steam API.
    Decodes the result and returns it as a dict.
    '''
    query = dict(params, key=APIKEY)
    req = '{}?{}'.format(url, urlencode(query))
    logging.debug(req)
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
    logging.debug('')
    url = build_endpoint('/'.join([DOTA2_MATCH, 'GetLiveLeagueGames', 'v1']))
    data = yield async_request(url)
    #logging.debug(data) #TODO: remove
    return data

@gen.coroutine
def get_heroes():
    '''
    Calls GetHeroes to get the list of hero IDs and names
    '''
    logging.debug('')
    url = build_endpoint('/'.join([DOTA2_ECON, 'GetHeroes', 'v1']))
    data = yield async_request(url)
    logging.debug(data) #TODO: remove
    return data

@gen.coroutine
def get_league_listing():
    '''
    Calls GetLeagueListing for data of DotaTV supported leagues.
    Returns a list of leagues
    '''

    logging.debug('')
    url = build_endpoint('/'.join([DOTA2_MATCH, 'GetLeagueListing', 'v1']))
    data = yield async_request(url)
    #logging.debug(data) #TODO: remove
    return data

@gen.coroutine
def get_ugc_file_details(ugcid):
    '''
    Get UGC file details (filename, download path) for a Dota2 UGC File
    '''

    logging.debug('')
    url = build_endpoint('/'.join([STEAM_REMOTE_STORAGE, 
        'GetUGCFileDetails', 'v1']))
    data = yield async_request(url, {
        'appid': DOTA2_ID,
        'ugcid': str(ugcid),
    })
    return data
