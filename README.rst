======================
bitfinex-python-client
======================

Python package to communicate with the bitfinex.net API.

Compatible with Python 2.7+ and Python 3.3+


Overview
========

There are two classes. One for the public part of API and a second for the
trading part.

Public class doesn't need user credentials, because API commands which this
class implements are not bound to bitfinex user account.

Description of API: https://www.bitfinex.com/pages/api


Install
=======

I don't know how to do this well. I'm guessing this:

Install from git::

    pip install git+git://github.com/streblo/bitfinex-python-client.git


Usage
=====

Here's a quick example of usage::

    >>> import bitfinex.client

    >>> public_client = bitfinex.client.Public()
    >>> print(public_client.ticker()['volume'])
    8700.01208078

    >>> trading_client = bitfinex.client.Trading(
    ...     username='999999', key='xxx', secret='xxx')
    >>> print(trading_client.account_balance()['fee'])
    0.5000
    >>> print(trading_client.ticker()['volume'])   # Can access public methods
    8700.01208078



How to activate a new API key
=============================

Get the API key from the website, most likely


Class diagram
=============
.. image:: https://raw.github.com/streblo/bitfinex-python-client/master/class_diagram.png
   :alt: Class diagram
   :align: center
