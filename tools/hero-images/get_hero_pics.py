#!/usr/bin/python3
'''
At the time of writing, this script reads a HAR file obtained from 
the network requests tab of "www.dota2.com/heroes/".
The requests of hero images are extracted and downloaded into
the current directory.
Images are renamed to their hero ID as specified from Steam API GetHeroes
'''
from urllib import request
import json
import sys
import os
from os.path import basename

APIKEY = os.environ.get('STEAM_APIKEY')

def dl_image(req_url):
    fname = basename(req_url)
    fname = fname.partition("?")[0]
    print("Retrieving {}".format(fname))
    furl = request.urlopen(req_url)
    with open(fname, 'wb') as fp:
        fp.write(furl.read())

if len(sys.argv) < 2:
    exit(('Specify the HAR file containing network requests of the'
        'dota2.com heropedia'))

fin = sys.argv[1]
with open(fin, 'r') as fp:
    data = json.load(fp)

num_retrieved = 0
for entry in data['log']['entries']:
    try:
        req_url = entry['request']['url']
        if "_sb.png" in req_url:
            num_retrieved += 1
            dl_image(req_url)
    except KeyError:
        pass

BASE_URL = 'http://api.steampowered.com'
DOTA2_ID = '570'
DOTA2_MATCH = 'IDOTA2Match_' + DOTA2_ID
DOTA2_ECON = 'IEconDOTA2_' + DOTA2_ID
#Rename images to hero IDs
furl = request.urlopen('/'.join([BASE_URL, DOTA2_ECON, 'GetHeroes',
    'v1?key={}'.format(APIKEY)]))
heroes = json.loads(furl.read().decode())
for hero in heroes['result']['heroes']:
    heroname = hero['name'].replace('npc_dota_hero_', '')
    fname = "{}_sb.png".format(heroname)
    newname = "{}.png".format(hero['id'])
    print("Renaming {} to {}".format(fname, newname))
    os.rename(fname, newname)

print("{} hero images retrieved".format(num_retrieved))
