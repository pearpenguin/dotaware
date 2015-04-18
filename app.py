import logging
from tornado import ioloop
import steamapi

def main():
    #Setup logging to file
    logger = logging.getLogger('dotaware')
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
    update_games = ioloop.PeriodicCallback(
        steamapi.get_live_league_games, 10000)
    update_games.start()
    loop = ioloop.IOLoop.instance()
    loop.start()

if __name__ == '__main__':
    main()
