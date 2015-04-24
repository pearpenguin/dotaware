import logging
import unittest
import steamapi
from tornado.testing import AsyncTestCase, gen_test
from tornado.ioloop import IOLoop
from tornado.httpclient import AsyncHTTPClient

logger = logging.getLogger('dotaware')
TEST_URL = ('http://api.steampowered.com/IDOTA2Match_570/'
    'GetLiveLeagueGames/v1')

class EndpointsTestCase(AsyncTestCase):
    '''
    Test the URL builder.
    Test the availability of APIs and do sanity checks on them
    '''

    def test_url_builder(self):
        '''
        Requires update if the tested API ever changes
        '''
        url = steamapi.build_endpoint('/'.join(
            ['IDOTA2Match_570', 'GetLiveLeagueGames', 'v1']))
        self.assertEqual(TEST_URL, url)
    
    @gen_test
    def test_async_request_success(self):
        '''
        Test it runs properly on a known endpoint
        '''
        #Make AsyncHTTPClient use this test's IOLoop
        steamapi.CLIENT = AsyncHTTPClient(self.io_loop)
        #Check that the request is logged as DEBUG
        with self.assertLogs(logger, logging.DEBUG) as log:
            data = yield steamapi.async_request(TEST_URL)
        self.assertTrue(isinstance(data, dict))
        req = '{}?key={}'.format(TEST_URL, steamapi.APIKEY)
        self.assertEqual(len(log.records), 1)
        self.assertEqual(req, log.records[0].getMessage())

    #def test_get_live_league_games(self):
    #    data = steamapi.get_live_league_games()
    #    self.assertEqual(type(data), dict)
    #    #TODO: Test the returned response

if __name__ == '__main__':
    unittest.main()
