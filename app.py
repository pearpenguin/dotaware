import logging
from tornado import ioloop, gen
import steamapi

logger = logging.getLogger('dotaware')

class Dota:
    def __init__(self):
        self.games = []
        self.simple_games = []

    def summarize_games(self, games):
        '''
        Remove scoreboard details from get_live_games(), making a small
        summarized list suitable for public serving
        '''
        def summarize(game):
            try:
                game['duration'] = game['scoreboard']['duration']
                del game['scoreboard']
            except KeyError:
                pass
            return game
            
        return list(map(summarize, games))
        
    @gen.coroutine
    def get_live_games(self):
        res = yield steamapi.get_live_league_games()
        self.games = res['result']['games']
        self.simple_games = self.summarize_games(self.games)

def main():
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
    dota = Dota()
    updater = ioloop.PeriodicCallback(dota.get_live_games, 10000)
    updater.start()
    loop = ioloop.IOLoop.current()
    loop.start()

if __name__ == '__main__':
    main()
