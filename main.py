#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from flask_caching import Cache
from flask import Flask, Response, request


app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
cache_timeout = 60 * 60 * 24 * 7 # 7 days


@app.route('/')
@cache.cached(timeout=cache_timeout)
def hello():
    return 'usage: {0}*plan_id*.ics<br /><br />for plan_id see: https://trv.no > search > its the latter part of the url (numeric)'.format(request.base_url)

@app.route('/<plan_id>.ics')
@cache.cached(timeout=cache_timeout)
def calendar(plan_id):
    cal = str(fetch_plan(plan_id))
    hax = cal.split('\n')
    
    # hax 2k18 :-)
    hax.insert(2, 'X-FROM-URL:{0}\r'.format(request.base_url))
    hax.insert(3, 'X-WR-RELCALID:TRV Tømmeplan\r')
    hax.insert(4, 'X-WR-CALNAME:TRV Tømmeplan\r')
    hax.insert(5, 'X-WR-TIMEZONE:Europe/Oslo\r')
    resp = '\n'.join(hax)

    return Response(resp, mimetype='text/calendar')

def fetch_plan(plan_id):
    url = 'https://trv.no/plan/{0}/'.format(plan_id)
    page = requests.get(url).text

    soup = BeautifulSoup(page, 'html.parser')
    table = soup.find("table", {"class": "bins"})
    c = Calendar()
    c.creator = 'https://github.com/jkaberg/trv-ical-server'

    for table_row in table.select('tbody tr'):
        year_data = table_row["class"]

        cells = table_row.findAll('td')

        if len(cells) > 0:
            year = year_data[0].split('-')[1]

            if len(year_data) > 1 and year_data[1] == 'first-of-new-year':
                start_year = int(year) - 1
            else:
                start_year = year

            dates = cells[2].text.split(' - ')
            week = cells[0].text.strip()
            trv_type = cells[1].text.strip()

            start = dates[0].split('.')
            end = dates[1].split('.')

            e = Event()
            e.name = trv_type
            e.begin = '{0}{1}{2} 00:00:00'.format(start_year, start[1], start[0])
            e.end = '{0}{1}{2} 00:00:00'.format(year, end[1], end[0])
            c.events.add(e)

    return c
