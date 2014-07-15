import json
import hmac
import hashlib
import time
import requests
import base64


class BitfinexError(Exception):
    pass


class BaseClient(object):
    """
    A base class for the API Client methods that handles interaction with
    the requests library.
    """
    #api_url = 'https://bf1.apiary-mock.com/'
    api_url = 'https://api.bitfinex.com/'
    exception_on_error = True

    def __init__(self, proxydict=None, *args, **kwargs):
        self.proxydict = proxydict

    def _get(self, *args, **kwargs):
        """
        Make a GET request.
        """
        return self._request(requests.get, *args, **kwargs)

    def _post(self, *args, **kwargs):
        """
        Make a POST request.
        """
        data = self._default_data()
        data.update(kwargs.get('data') or {})
        kwargs['data'] = data
        return self._request(requests.post, *args, **kwargs)

    def _default_data(self):
        """
        Default data for a POST request.
        """
        return {}

    def _request(self, func, url, *args, **kwargs):
        """
        Make a generic request, adding in any proxy defined by the instance.

        Raises a ``requests.HTTPError`` if the response status isn't 200, and
        raises a :class:`BitfinexError` if the response contains a json encoded
        error message.
        """
        return_json = kwargs.pop('return_json', False)
        url = self.api_url + url
        response = func(url, *args, **kwargs)

        if 'proxies' not in kwargs:
            kwargs['proxies'] = self.proxydict
            
        #print 'Response Code: ' + str(response.status_code) 
        #print 'Response Header: ' + str(response.headers)
        #print 'Response Content: '+ str(response.content)

        # Check for error, raising an exception if appropriate.
        response.raise_for_status()

        try:
            json_response = response.json()
        except ValueError:
            json_response = None
        if isinstance(json_response, dict):
            error = json_response.get('error')
            if error:
                raise BitfinexError(error)

        if return_json:
            if json_response is None:
                raise BitfinexError(
                    "Could not decode json for: " + response.text)
            return json_response

        return response


class Public(BaseClient):

    def ticker(self):
        """
        Returns dictionary. 
        
        mid (price): (bid + ask) / 2
        bid (price): Innermost bid.
        ask (price): Innermost ask.
        last_price (price) The price at which the last order executed.
        low (price): Lowest trade price of the last 24 hours
        high (price): Highest trade price of the last 24 hours
        volume (price): Trading volume of the last 24 hours
        timestamp (time) The timestamp at which this information was valid.
        
        """
        return self._get("v1/pubticker/btcusd", return_json=True)


class Trading(Public):

    def __init__(self, key, secret, *args, **kwargs):
        """
        Stores the username, key, and secret which is used when making POST
        requests to Bitfinex.
        """
        super(Trading, self).__init__(
                 key=key, secret=secret, *args, **kwargs)
        self.key = key
        self.secret = secret

    def get_nonce(self):
        """
        Get a unique nonce for the bitfinex API.

        This integer must always be increasing, so use the current unix time.
        Every time this variable is requested, it automatically increments to
        allow for more than one API request per second.

        This isn't a thread-safe function however, so you should only rely on a
        single thread if you have a high level of concurrent API requests in
        your application.
        """
        nonce = getattr(self, '_nonce', 0)
        if nonce:
            nonce += 1
        # If the unix time is greater though, use that instead (helps low
        # concurrency multi-threaded apps always call with the largest nonce).
        self._nonce = max(int(time.time()), nonce)
        return self._nonce

    def _default_data(self, *args, **kwargs):
        """
        Generate a one-time signature and other data required to send a secure
        POST request to the Bitfinex API.
        """
        data = {}
        nonce = self.get_nonce()
        data['nonce'] = str(nonce)
        data['request'] = args[0]
        return data

    def _post(self, *args, **kwargs):
        """
        Make a POST request.
        """
        data = kwargs.pop('data', {})
        data.update(self._default_data(*args, **kwargs))
        
        key = self.key
        secret = self.secret
        payload_json = json.dumps(data)
        payload = base64.b64encode(payload_json)
        sig = hmac.new(secret, payload, hashlib.sha384)
        sig = sig.hexdigest()

        headers = {
           'X-BFX-APIKEY' : key,
           'X-BFX-PAYLOAD' : payload,
           'X-BFX-SIGNATURE' : sig
           }
        kwargs['headers'] = headers
        
        #print("headers: " + json.dumps(headers))
        #print("sig: " + sig)
        #print("api_secret: " + secret)
        #print("api_key: " + key)
        #print("payload_json: " + payload_json)
        return self._request(requests.post, *args, **kwargs)

    def account_infos(self):
        """
        Returns dictionary::
        [{"fees":[{"pairs":"BTC","maker_fees":"0.1","taker_fees":"0.2"},
        {"pairs":"LTC","maker_fees":"0.0","taker_fees":"0.1"},
        {"pairs":"DRK","maker_fees":"0.0","taker_fees":"0.1"}]}]
        """
        return self._post("/v1/account_infos", return_json=True)

    def user_transactions(self, offset=0, limit=100, descending=True):
        """
        Returns descending list of transactions. Every transaction (dictionary)
        contains::

            {u'usd': u'-39.25',
             u'datetime': u'2013-03-26 18:49:13',
             u'fee': u'0.20', u'btc': u'0.50000000',
             u'type': 2,
             u'id': 213642}
        """
        data = {
            'offset': offset,
            'limit': limit,
            'sort': 'desc' if descending else 'asc',
        }
        return self._post("user_transactions/", data=data, return_json=True)

    def open_orders(self):
        """
        Returns JSON list of open orders. Each order is represented as a
        dictionary.
        """
        return self._post("open_orders/", return_json=True)





