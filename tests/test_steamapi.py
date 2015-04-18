import unittest
import steamapi
from tornado.ioloop import IOLoop

class EndpointsTestCase(unittest.TestCase):
    '''
    Test the URL builder.
    Test the availability of APIs and do sanity checks on them
    '''

    def test_url_builder(self):
        '''
        Requires update if the tested API ever changes
        '''
        TEST_URL = ('http://api.steampowered.com/IDOTA2Match_570/'
            'GetLiveLeagueGames/v1?key={}').format(steamapi.APIKEY)
        url = steamapi.build_request('/'.join(
            ['IDOTA2Match_570', 'GetLiveLeagueGames', 'v1']))
        self.assertEqual(TEST_URL, url)
    
    #TODO: need tornado IOLoop to test coroutines
#    def test_get_live_league_games(self):
#        data = steamapi.get_live_league_games()
#        self.assertEqual(type(data), dict)
#        #TODO: Test the returned response
#
if __name__ == '__main__':
    unittest.main()
