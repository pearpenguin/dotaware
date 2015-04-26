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

def make_simple_game(game):
    '''
    Make a summarized game dict without the scoreboard
    '''
    try:
        simple_game = dict(game)
        simple_game['duration'] = simple_game['scoreboard']['duration']
        del simple_game['scoreboard']
    except KeyError:
        pass #Games that haven't started have no scoreboard

    return simple_game

def make_update(game):
    '''
    Make an update dict (summarized) for the specified game dict
    '''

    def extract_team_stat(team):
        '''
        Extract certain fields from the scoreboard
        '''
        try:
            return {
                'score': team['score'],
                'tower_state': team['tower_state'],
                'barracks_state': team['barracks_state'],
            }
        except KeyError:
            #TODO: API may have changed, log/inform devs
            return {}

    update = {}
    try:
        update['spectators'] = game['spectators']
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
    inactive_games = {}
    #Summarized games (without detailed scoreboard)
    simple_games = {}
    #All connected WebSocket clients
    clients = set()

    def open(self):
        logging.debug("Dota WebSocket opened")
        self.clients.add(self)
        self.send_simple_games()

    def on_close(self):
        logging.debug("Dota WebSocket closed")
        self.clients.remove(self)

    def send_simple_games(self):
        '''
        Send the summarized games dict to this client
        '''
        self.write_message({'simple_games': self.simple_games})

    def send_updates(self, updates, new_games={}):
        '''
        Send dict of updates to this client
        '''
        self.write_message({
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
        active_games = {} #New dict of games
        updates = {} #Compact dict to update clients
        new_games = {} #New games not seen before, send as simple_game
        for game in games:
            try:
                match_id = game['match_id']
            except KeyError:
                #TODO: log + notify devs, API may have changed
                pass
            active_games[match_id] = game
            #Summarize the game by removing scoreboard
            simple_game = make_simple_game(game)
            cls.simple_games[match_id] = simple_game
            #Remove games which are still active, leftover are inactive
            if match_id in cls.active_games:
                del cls.active_games[match_id]
                #Make compact update dict with minimal info
                updates[match_id] = make_update(game)
            else:
                #Make note of any new games, to be sent to clients
                new_games[match_id] = simple_game

        #Sync the inactive/active games
        cls.inactive_games.update(cls.active_games)
        cls.active_games = active_games
        
        #Update all clients with new game states
        cls.update_clients(updates, new_games)

class WebHandler(RequestHandler):

    def get(self):
        self.write('<p>{}</p>'.format(repr(DotaHandler.active_games)))

def main():
    #Setup root logger to log to file
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fhandler = logging.FileHandler('dotaware.log')
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] (%(funcName)s): %(message)s')
    fhandler.setFormatter(formatter)
    logger.addHandler(fhandler)
    #Log levels more than WARNING to stderr as well
    handler = logging.StreamHandler()
    handler.setLevel(logging.WARNING)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
        
    logging.info('Starting Dotaware')
    #Setup the Dota games manager and periodic updaters
    updater = ioloop.PeriodicCallback(get_live_dota_games, 10000)
    updater.start()
    #Start app
    app = Application([
        URLSpec(r'/', WebHandler),
        URLSpec(r'/dota', DotaHandler),
    ])
    app.listen(8080)
    loop = ioloop.IOLoop.current()
    loop.start()

if __name__ == '__main__':
    main()
