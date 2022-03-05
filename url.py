import urllib.parse

def encode(url):
    return urllib.parse.quote_plus(url)

def decode(encoded_url):
    return urllib.parse.unquote_plus(encoded_url)
