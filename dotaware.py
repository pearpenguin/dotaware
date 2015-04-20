import logging
import tornado.gen
from tornado.web import RequestHandler, Application, URLSpec
from tornado import ioloop
import steamapi

logger = logging.getLogger('dotaware')

class Dota:
    def __init__(self):
        #Live games
        self.active_games = {}
        #Completed games but not yet persisted into DB
        self.inactive_games = {}
        self.simple_games = []

    def sync_games(self, games):
        '''
        Synchronize active/inactive games dicts
        Also remove scoreboard details, making a small
        summarized list suitable for public serving.
        '''
        live_games = {} #Detailed dict
        simple_games = [] #summarized list
        for game in games:
            try:
                match_id = game['match_id']
            except KeyError:
                #TODO: log + notify devs, API may have changed
                pass
            #Remove games which are still active, leftover are inactive
            try:
                del self.active_games[match_id]
            except KeyError:
                pass
            live_games[match_id] = game
            try:
                simple_game = dict(game)
                simple_game['_duration'] = simple_game['scoreboard']['duration']
                del simple_game['scoreboard']
            except KeyError:
                pass #Games that haven't started have no scoreboard
            simple_games.append(simple_game)

        self.simple_games = simple_games
        #Sync the inactive/active games
        self.inactive_games.update(self.active_games)
        self.active_games = live_games

    @tornado.gen.coroutine
    def get_live_games(self):
        res = yield steamapi.get_live_league_games()
        games = res['result']['games']
        self.sync_games(games)

class WebHandler(RequestHandler):

    def initialize(self, dota):
        self.dota = dota

    def get(self):
        self.write('<p>Testing</p>')

def main():
    #TODO: setup root logger to log to file as well as stdout (for tornado logs)
    #Setup logging to file
    logger.setLevel(logging.DEBUG)
    logger.propagate = False #Don't use root logger at all
    fhandler = logging.FileHandler('dotaware.log')
    formatter = logging.Formatter(
        '%(asctime)s (%(funcName)s): [%(levelname)s] %(message)s')
    fhandler.setFormatter(formatter)
    logger.addHandler(fhandler)
    #Log levels more than WARNING to stderr (don't rely on root logger)
    handler = logging.StreamHandler()
    handler.setLevel(logging.WARNING)
    logger.addHandler(handler)
        
    logger.info('Starting Dotaware')
    #Setup the Dota games manager and periodic updaters
    dota = Dota()
    updater = ioloop.PeriodicCallback(dota.get_live_games, 10000)
    updater.start()
    #Start app
    app = Application([URLSpec(r'/', WebHandler, {'dota': dota})])
    app.listen(8080)
    loop = ioloop.IOLoop.current()
    loop.start()

if __name__ == '__main__':
    main()
