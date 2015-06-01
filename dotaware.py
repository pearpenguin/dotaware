import logging
import tornado.gen
import os.path
from tornado.web import RequestHandler, Application, URLSpec
from tornado.websocket import WebSocketHandler
from tornado import ioloop
import steamapi

#Real path to static dir
WEB_STATIC_PATH = "./static"
LOGOS_DIR = '/'.join([WEB_STATIC_PATH, 'img', 'team-logos'])
#Mount directory for static dir (relative to site root)
WEB_STATIC_MOUNT = "static"
LOOP = ioloop.IOLoop.current()

def convert_to_url(static_path):
    '''
    Convert a static path relative to CWD (or absolute path)
    to a public accessible URL.
    '''
    return static_path.replace(WEB_STATIC_PATH, '/'+WEB_STATIC_MOUNT, 1)
    
@tornado.gen.coroutine
def get_dota_leagues():
    res = yield steamapi.get_league_listing()
    try:
        leagues = res['result']['leagues']
    except KeyError:
        logging.error("Unexpected format in SteamAPI call")
    DotaHandler.sync_leagues(leagues)
    
@tornado.gen.coroutine
def get_live_dota_games():
    res = yield steamapi.get_live_league_games()
    try:
        games = res['result']['games']
    except KeyError:
        logging.error("Unexpected format in SteamAPI call")
        #TODO: inform devs
    DotaHandler.sync_games(games)

@tornado.gen.coroutine
def dl_team_logo(team_id, path, logo_id):
    '''
    Retrieve the URL for the team logo using Steam API UGC file info.
    Download the logo and save to static path
    '''
    logging.debug("Downloading logo to '{}' (logo_id = {})".format(path, logo_id))
    ugc_data = yield steamapi.get_ugc_file_details(logo_id)
    logo = yield steamapi.request(ugc_data['data']['url'])
    with open(path, 'wb') as f:
        f.write(logo)

def init_team_logo(team_id, *args):
    '''
    Initial retrieval of team logo requires signalling the DotaHandler
    '''
    logging.debug("Initializing team logo for team '{}'".format(team_id))
    dl_team_logo(team_id, *args)
    DotaHandler.add_team_logo(team_id)

def get_logo_path(team_id):
    '''
    Return the path (relative to CWD) to this team's logo
    '''

    return "{}/{}".format(LOGOS_DIR, team_id)

def add_team_logo(team):
    '''
    Add the logo path to a team dictionary.
    Schedule request to download the logo if not available.
    '''
    try:
        #Team has no logo (UGC ID of 0 means unavailable)
        if not team['team_logo']:
            return
    except KeyError:
        return

    team_id = team['team_id']
    path = get_logo_path(team_id)
    #Convert path to public URL
    url = convert_to_url(path)
    if os.path.isfile(path):
        team['logo_url'] = url
    else:
        LOOP.add_callback(init_team_logo, team_id, path, team['team_logo'])
        
    

def extract_team_stat(team):
    '''
    Extract a team scoreboard in the 'scoreboard' key
    '''
    def sort_player_key(player):
        return int(player['player_slot'])

    try:
        #Sort players into order and only retain account_id key
        sorted_players = sorted(team['players'], key=sort_player_key)
        players = []
        for player in sorted_players:
            players.append({'account_id': player['account_id']})
            
        return {
            'score': team['score'],
            'tower_state': team['tower_state'],
            'barracks_state': team['barracks_state'],
            #TODO: don't update players if duration > 0
            'players': players,
        }
    except KeyError:
        #TODO: API may have changed, log/inform devs
        return {}


class DotaHandler(WebSocketHandler):

    #Live games
    active_games = {}
    #Completed games but not yet persisted into DB
    inactive_games = {} #TODO: persist inactive games
    #Summarized games (without detailed scoreboard)
    simple_games = {}
    #League listing
    leagues = {}
    #Ref counted leagues with currently active games
    leagues_refcnt = {}
    #Active leagues
    active_leagues = {}
    #Recently downloaded logos, inform clients
    logos_to_add = set()
    #All connected WebSocket clients
    clients = set()

    def open(self):
        logging.debug("Dota WebSocket opened")
        self.clients.add(self)
        self.send_updates(new_games=self.simple_games, 
            new_leagues=self.active_leagues)

    def on_close(self):
        logging.debug("Dota WebSocket closed")
        self.clients.remove(self)

    def send_updates(self, updates={}, new_games={}, new_leagues={}):
        '''
        Send dict of updates and/or new games to this client
        '''
        self.write_message({
            'event': 'dota.update_list',
            'updates': updates,
            'new_games': new_games,
            'new_leagues': new_leagues,
        })

    @classmethod
    def make_simple_game(cls, game, update=None):
        '''
        Make a summarized game dict without the scoreboard (for new games)
        If available, include static path to team logo. Otherwise schedule
        Steam API request to download the team logo.
        '''

        simple_game = dict(game)
        try:
            del simple_game['scoreboard']
        except KeyError:
            pass #Games that haven't started have no scoreboard
        try:
            add_team_logo(simple_game['radiant_team'])
        except KeyError:
            pass
        try:
            add_team_logo(simple_game['dire_team'])
        except KeyError:
            pass
        if update is None:
            update = cls.make_update(game)
        simple_game.update(update)

        return simple_game

    @classmethod
    def init_logos(cls, update, game):
        '''
        Checks whether new logos were downloaded and need to be
        made known to the client via an update
        '''

        def add_to_team(cls, team):
            team_id = team['team_id']
            if team_id in cls.logos_to_add:
                logging.debug("Adding logo URL for team '{}'".format(team_id))
                add_team_logo(team)
                cls.logos_to_add.remove(team_id)
                return True
            return False

        if 'radiant_team' in game:
            if add_to_team(cls, game['radiant_team']):
                update['radiant_team'] = game['radiant_team']
        if 'dire_team' in game:
            if add_to_team(cls, game['dire_team']):
                update['dire_team'] = game['dire_team']
        
    @classmethod
    def make_update(cls, game):
        '''
        Make an update dict (summarized) for the specified game dict
        '''

        update = {}
        try:
            update['spectators'] = game['spectators']
            update['players'] = game['players']
            #Add team logo URLs if needed
            cls.init_logos(update, game)
            #Simplify the scoreboard
            if 'scoreboard' in game:
                scoreboard = {}
                scoreboard['duration'] = game['scoreboard']['duration']
                scoreboard['radiant'] = extract_team_stat(
                    game['scoreboard']['radiant'])
                scoreboard['dire'] = extract_team_stat(
                    game['scoreboard']['dire'])
                update['scoreboard'] = scoreboard
        except KeyError:
            #TODO: API may have changed, log/inform devs
            pass
        return update

    @classmethod
    def add_team_logo(cls, team_id):
        '''
        Send URL of teams logo on the next update packet if required
        '''
        logging.debug("Adding {} to logos_to_add".format(team_id))
        cls.logos_to_add.add(team_id)

    @classmethod
    def build_active_leagues(cls):
        '''
        Builds the league info of currently active leagues
        '''
        for league_id in cls.leagues_refcnt:
            try:
                cls.active_leagues[league_id] = cls.leagues[league_id]
            except KeyError:
                #League listing is not up to date
                # TODO: schedule an update of new leagues
                pass

    @classmethod
    def update_clients(cls, updates, new_games, new_leagues):
        '''
        Update clients with new game states, new active leagues,
        and leagues to remove
        '''

        logging.debug("Updating {} Dota clients".format(len(cls.clients)))
        for client in cls.clients:
            client.send_updates(updates, new_games, new_leagues)

    @classmethod
    def sync_games(cls, games):
        '''
        Synchronize active/inactive games dicts
        Also remove scoreboard details, making a small
        summarized dict suitable for public serving.
        '''
        active_games = {} #Currently active games
        simple_games = {} #Currently active games
        updates = {} #Compact dict to update clients
        new_games = {} #New games not seen before, send as simple_game
        new_leagues = {} #New active leagues
        for game in games:
            try:
                match_id = game['match_id']
                league_id = game['league_id']
            except KeyError:
                #TODO: log + notify devs, API may have changed
                pass
            active_games[match_id] = game
            #Make compact update dict with minimal info
            update = cls.make_update(game)
            #Summarize the game by removing scoreboard and add update
            simple_game = cls.make_simple_game(game, update)
            simple_games[match_id] = simple_game
            #Remove games which are still active, leftover are inactive
            if match_id in cls.active_games:
                #Send the update packet
                updates[match_id] = update
                del cls.active_games[match_id]
            else:
                #Make note of any new games, to be sent to clients
                new_games[match_id] = simple_game
                #New games require no update packet
                #Find the league this game belongs to, increase refcnt
                try:
                    cls.leagues_refcnt[league_id] += 1
                except KeyError:
                    cls.leagues_refcnt[league_id] = 1
                    # Leagues may not be up to date yet
                    if league_id in cls.leagues:
                        new_leagues[league_id] = cls.leagues[league_id]

        #TODO: refactor the cleanup of inactive games
        #Lower refcnt for leagues in which games have become inactive
        for game in cls.active_games.values():
            try:
                league_id = game['league_id']
            except KeyError:
                pass #TODO log + notify devs, API may have changed
            cls.leagues_refcnt[league_id] -= 1
            if cls.leagues_refcnt[league_id] == 0:
                del cls.leagues_refcnt[league_id]

        #Build currently active leagues
        cls.build_active_leagues()
        #Sync the inactive/active games
        cls.inactive_games.update(cls.active_games)
        cls.active_games = active_games
        cls.simple_games = simple_games
        
        #Update all clients with new game states
        #logging.debug(new_leagues) #TODO: remove
        #logging.debug(cls.active_leagues) #TODO: remove
        cls.update_clients(updates, new_games, new_leagues)

    @classmethod
    def sync_leagues(cls, leagues):
        '''
        Syncs leagues from Steam API
        '''

        try:
            cls.leagues = {l['leagueid']: l for l in leagues}
            #logging.debug(cls.leagues) #TODO: remove
        except KeyError:
            pass #TODO: log + inform devs (API changed?)

class WebHandler(RequestHandler):

    def get(self):
        self.write('<p>{}</p>'.format(repr(DotaHandler.active_games)))

def main():
    #Setup directories that are not versioned
    if not os.path.isdir(LOGOS_DIR):
        os.makedirs(LOGOS_DIR)
    #Setup root logger to log to file
    logger = logging.getLogger()
    #Clear any handlers that may have been configured by imports
    logger.handlers = []
    logger.setLevel(logging.DEBUG)
    fhandler = logging.FileHandler('dotaware.log')
    formatter = logging.Formatter(
        '[%(levelname)s] %(asctime)s (%(module)s.%(funcName)s): %(message)s')
    fhandler.setFormatter(formatter)
    logger.addHandler(fhandler)
    #Log levels more than WARNING to stdout as well
    handler = logging.StreamHandler()
    handler.setLevel(logging.WARNING)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
        
    logging.info('Starting Dotaware')
    #Setup the Dota games manager and periodic updaters
    updater = ioloop.PeriodicCallback(get_live_dota_games, 10000)
    updater.start()
    #ioloop.PeriodicCallback(get_dota_leagues, 30000).start()
    get_dota_leagues()
    #Start app
    app = Application(
        [
            URLSpec(r'/', WebHandler),
            URLSpec(r'/dota', DotaHandler),
        ],
        static_path=WEB_STATIC_PATH,
        debug=True
    )
    app.listen(8080)
    LOOP.start()

if __name__ == '__main__':
    main()
