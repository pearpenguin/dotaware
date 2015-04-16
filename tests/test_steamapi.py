import unittest
import steamapi

class EndpointsTestCase(unittest.TestCase):
    '''
    Test the URL builder.
    Test the availability of APIs does sanity checks on them
    '''

    def test_url_builder(self):
        '''
        Requires update if this API ever changes
        '''
        TEST_URL = ('http://api.steampowered.com/IDOTA2Match_570/'
            'GetLiveLeagueGames/v1')
        url = steamapi.build_endpoint('/'.join(
            ['IDOTA2Match_570', 'GetLiveLeagueGames', 'v1']))
        self.assertEqual(TEST_URL, url)
    
    def test_get_live_league_games(self):
        data = steamapi.get_live_league_games()
        self.assertEqual(type(data), dict)

if __name__ == '__main__':
    unittest.main()
