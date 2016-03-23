import urllib
import json as simplejson

import time
import io
import os

"""
the wikipedia api url that is queried.
Note: This can change and therefore should be updated to the latest url 
%s defines the language eg. en for english, fr for french etc.
"""
api_url = 'https://%s.wikipedia.org/w/api.php'

def _unicode_urlencode(params):
    """
    A unicode aware version of urllib.urlencode.
    Borrowed from pyfacebook :: http://github.com/sciyoshi/pyfacebook/
    """
    if isinstance(params, dict):
        params = params.items()
    return urllib.urlencode([(k, isinstance(v, unicode) and v.encode('utf-16') or v) for k, v in params])

def _run_query(args, language, retry=5, wait=5):
    """
    takes arguments and optional language argument and runs query on server
    if a socket error occurs, wait the specified seconds of time and retry for the specified number of times
    """
    url = api_url % (language)
    data = _unicode_urlencode(args)
    while True:
        try:
            search_results = urllib.urlopen(url, data=data)
            json = simplejson.loads(search_results.read())
        except Exception:
            if not retry:
                json = None
                break
            retry -= 1
            time.sleep(wait)
        else:
            break
    return json

"""
method used to query for raw article text
@param name:
    the name/title of the article
@param lang:
    the language being used for the article title and text
"""
def query_text_raw(title, language='en'):
    """
    action=query
    Fetches the article in wikimarkup form
    """
    query_args = {
        'action': 'query',
        'titles': title,
        'explaintext': True,
        'prop': 'extracts',
        'format': 'json',
        'redirects': ''
    }
    json = _run_query(query_args, language)
    if not json == None:
        for page_id in json['query']['pages']:
            if page_id != '-1' and 'missing' not in json['query']['pages'][page_id]:
                response = {
                    'text': json['query']['pages'][page_id]['extract']
                }
                return response
    return None

"""
method to generate a list of the languages queried from wikipedia
"""
def create_lang_list(filename):
    f = open(filename, "r")
    lang = f.readline().strip("\r\n").split("\t")
    f.close()
    return lang

"""
method to write given text to the file defined by filename
also takes care of creating a directory if it doesn't exist 
@param filename:
    string containing the name of the file where data needs to be stored
@param text:
    string containing the data that needs to be written to file
@param language:
    string denoting the language required to save the file in the appropriate language folder
@param datatype:
    string denoting the directory where the file needs to be saved
"""
def write_content_to_file(filename, text, language, datatype):
    # TODO: need to escape "/" from filenames (might need to replace them with "-")
    filepath = "data/%s/%s/%s.txt" %(datatype, language, filename)
    d = os.path.dirname(filepath)

    if not os.path.exists(d):
        os.makedirs(d)

    f = open(filepath, "w")
    f.write(text.encode('utf-16'))
    f.close()

"""
method responsible for reading the file one line at a time 
and then querying for the raw article data and backlinks linking to that data

Note: it is done this way because there is no way to maintain state of the file in an efficient manner 
without looping through the entire file every time

@param filename:
    string denoting the name of the file that needs to be read line by line
@param languages:
    a list of languages as retrieved from wikipedia
"""
def read_file_by_line(filename, languages):
    f = open(filename, "r")
    for i, line in enumerate(f):
        if not i == 0:
            titles = line.strip("\r\n").split("\t")
            for index, lang in enumerate(languages):
                if not titles[index] == "":
                    article_resp = query_text_raw(titles[index], lang)
                    if not article_resp == None:
                        write_content_to_file("".join(titles[0].split()), article_resp['text'], lang, "articles")

                    backlink_resp = query_redirects(titles[index], lang)
                    if not backlink_resp == None:
                        write_content_to_file("".join(titles[0].split()), backlink_resp['backlinks'], lang, "backlinks")

"""
method used to query for redirect backlinks
@param name:
    the name/title of the article for which backlinks are requested
@param lang:
    the language being used for the article title
"""
def query_redirects(name, lang):
    query_args = {
        'action': 'query',
        'bltitle': name,
        'list': 'backlinks',
        'blfilterredir': 'redirects',
        'format': 'json',
        'bllimit': 500
    }

    json = _run_query(query_args, lang)
    if not json == None:
        backlinks = []
        for page_id in json['query']['backlinks']:
            backlinks.append(page_id['title'])
        
        if backlinks:
            response = {
                'backlinks' : "\n".join(backlinks)
            }    
            return response
    return None

"""
method used to write backlinks to the file
@param filename:
    the name/title of the article for which backlinks are being written
@param language:
    the language being used for the article title
@param text:
    the data that needs to be written to the file
"""
def create_or_append_backlink(language, filename, text):
    filepath = "data/backlinks/%s/%s.txt" %(language, filename)
    d = os.path.dirname(filepath)

    if not os.path.exists(d):
        os.makedirs(d)

    f = open(filepath, "a")
    f.write(text.encode("utf-16"))
    f.close()

"""
method used to artificially create a backlink for a particular name
useful when no other backlinks are present

the method simply reads the name from the namelist and appends it to the end of 
the other backlinks for this name, or creates a backlinks file if none exists
"""
def generate_name_backlinks(filename, languages):
    f = open(filename, "r")
    for i, line in enumerate(f):
        if not i == 0:
            titles = line.strip("\r\n").split("\t")
            for j, lang in enumerate(languages):
                if not titles[j] == "":
                    create_or_append_backlink(lang, "".join(titles[0].split()), titles[j])


if __name__ == "__main__":
    languages = create_lang_list("wikipedia-names")
    # read_file_by_line("wikipedia-names", languages)
    # generate_name_backlinks("wikipedia-names", languages)