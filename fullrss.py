#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Full-text version of an RSS-feed.'''

# Native
from multiprocessing import Pool
from os import path as osp
import sys
APP_PATH = osp.dirname(osp.realpath(__file__))
sys.path.insert(0, osp.join(APP_PATH, '.env/lib/python2.7/site-packages'))

# Vendor
# pylint: disable=locally-disabled,wrong-import-position,ungrouped-imports
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request, Response
from newspaper import Article
import flask
import requests

# pylint: disable=locally-disabled, invalid-name
__version__ = open(osp.join(APP_PATH, 'VERSION')).read().strip()

app = Flask(__name__)
application = app


def expand_feed(url):
    '''Expand a feed.'''
    soup = BeautifulSoup(get_feed(url), 'xml')
    items = soup.find_all('item')
    urls = [unicode(item.link.string) for item in items]

    pool = Pool()
    articles = pool.map(get_article_data, urls)

    for i, item in enumerate(items):
        update_item(soup, item, articles[i])
    return str(soup)


def get_feed(url):
    '''Return the feed content.'''
    # TODO: check if the feed has changed
    req = requests.get(url)
    return req.text


def get_article_data(url):
    '''Return article data. '''
    # TODO: check if the article has changed
    article = Article(url, keep_article_html=True, fetch_images=False)
    article.download()
    article.parse()
    return {
        'url': article.canonical_link,
        'creator': ', '.join(article.authors),
        'content': article.article_html
    }


def update_item(soup, item, data):
    '''Update an item.'''
    link = item.link
    if not link:
        link = soup.new_tag('link')
        item.append(link)
    link.string = data['url']

    creator = item.creator
    if not creator:
        creator = soup.new_tag('dc:creator')
        item.append(creator)
    creator.string = data['creator']

    content = item.encoded
    if not content:
        content = soup.new_tag('content:encoded')
        item.append(content)
    content.string = data['content']


@app.route('/ping')
def ping():
    '''Return the version of the app.'''
    return jsonify({
        'ok': True,
        'status': 'success',
        'data': {
            'version': __version__
        }
    })


@app.route('/', defaults={'url': ''})
def index(url):
    '''Return an RSS feed with the full-text in the description of the first
    five articles.

    Args:
        url (str): the URL to the RSS feed

    Returns:
        XML of the modified RSS feed
    '''
    url = (url or request.args.get('url') or '').strip()
    if not url:
        flask.abort(404)

    return Response(expand_feed(url), mimetype='text/xml')


if __name__ == "__main__":
    app.run(debug=False)
