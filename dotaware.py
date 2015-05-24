import logging
import tornado.gen
from tornado.web import RequestHandler, Application, URLSpec
from tornado.websocket import WebSocketHandler
from tornado import ioloop
import steamapi

@tornado.gen.coroutine
def get_live_dota_games():
    res = yield steamapi.get_live_league_games()
    games = res['result']['games']
    DotaHandler.sync_games(games)

def make_simple_game(game, update=None):
    '''
    Make a summarized game dict without the scoreboard (for new games)
    '''

    simple_game = dict(game)
    try:
        del simple_game['scoreboard']
    except KeyError:
        pass #Games that haven't started have no scoreboard
    if update is None:
        update = make_update(game)
    simple_game.update(update)

    return simple_game

def make_update(game):
    '''
    Make an update dict (summarized) for the specified game dict
    '''

    def extract_team_stat(team):
        '''
        Extract certain fields from the scoreboard
        '''
        def sort_player_key(player):
            return int(player['player_slot'])

        try:
            #Sort players into order and only retain account_id key
            sorted_players = sorted(team['players'], key=sort_player_key)
            players = []
            for player in sorted_players:
                players.append(player['account_id'])
                
            return {
                'score': team['score'],
                'tower_state': team['tower_state'],
                'barracks_state': team['barracks_state'],
                'players': players,
            }
        except KeyError:
            #TODO: API may have changed, log/inform devs
            return {}

    update = {}
    try:
        update['spectators'] = game['spectators']
        update['players'] = game['players']
        if 'scoreboard' in game:
            update['duration'] = game['scoreboard']['duration']
            update['radiant'] = extract_team_stat(
                game['scoreboard']['radiant'])
            update['dire'] = extract_team_stat(
                game['scoreboard']['dire'])
    except KeyError:
        #TODO: API may have changed, log/inform devs
        pass
    return update

class DotaHandler(WebSocketHandler):

    #Live games
    active_games = {}
    #Completed games but not yet persisted into DB
    inactive_games = {} #TODO: persist inactive games
    #Summarized games (without detailed scoreboard)
    simple_games = {}
    #All connected WebSocket clients
    clients = set()

    def open(self):
        logging.debug("Dota WebSocket opened")
        self.clients.add(self)
        self.send_updates(new_games=self.simple_games)

    def on_close(self):
        logging.debug("Dota WebSocket closed")
        self.clients.remove(self)

    def send_updates(self, updates={}, new_games={}):
        '''
        Send dict of updates and/or new games to this client
        '''
        self.write_message({
            'event': 'dota.update_list',
            'updates': updates,
            'new_games': new_games,
        })

    @classmethod
    def update_clients(cls, updates, new_games):
        '''
        Update clients with new game states and new games
        '''

        logging.debug("Updating {} Dota clients".format(len(cls.clients)))
        for client in cls.clients:
            client.send_updates(updates, new_games)

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
        for game in games:
            try:
                match_id = game['match_id']
            except KeyError:
                #TODO: log + notify devs, API may have changed
                pass
            active_games[match_id] = game
            #Make compact update dict with minimal info
            update = make_update(game)
            #Summarize the game by removing scoreboard and add update
            simple_game = make_simple_game(game, update)
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

        #Sync the inactive/active games
        cls.inactive_games.update(cls.active_games)
        cls.active_games = active_games
        cls.simple_games = simple_games
        
        #Update all clients with new game states
        cls.update_clients(updates, new_games)

class WebHandler(RequestHandler):

    def get(self):
        self.write('<p>{}</p>'.format(repr(DotaHandler.active_games)))

def main():
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
    #Start app
    app = Application(
        [
            URLSpec(r'/', WebHandler),
            URLSpec(r'/dota', DotaHandler),
        ],
        static_path="./static",
        debug=True
    )
    app.listen(8080)
    loop = ioloop.IOLoop.current()
    loop.start()

if __name__ == '__main__':
    main()
