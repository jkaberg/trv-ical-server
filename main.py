#!/usr/bin/python
# -*- coding: utf-8 -*-

import uuid
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from flask_caching import Cache
from flask import Flask, Response, request
from icalendar import Calendar, Event


app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
cache_timeout = 60 * 60 * 24 * 7 # 7 days


@app.route('/')
@cache.cached(timeout=cache_timeout)
def hello():
    return 'usage: {0}*plan_id*.ics<br /><br />for plan_id see: https://trv.no > search > its the latter part of the url (numeric)'.format(request.base_url)

@app.route('/<plan_id>.ics')
@cache.cached(timeout=cache_timeout)
def fetch_plan(plan_id):
    url = 'https://trv.no/plan/{0}/'.format(plan_id)
    page = requests.get(url).text

    soup = BeautifulSoup(page, 'html.parser')
    title = soup.find('title').string

    if title.startswith('Side ikke funnet') or len(page) == 0:
        return 'you sure this is an correct plan id?'

    table = soup.find("table", {"class": "bins"})

    c = Calendar()
    c.add('X-WR-RELCALID', 'TRV Tømmeplan')
    c.add('X-WR-CALNAME', 'TRV Tømmeplan')
    c.add('X-WR-TIMEZONE', 'Europe/Oslo')
    c.add('X-FROM-URL', '{0}'.format(request.base_url))
    c.add('X-AUTHOR', 'https://github.com/jkaberg/trv-ical-server')

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
            e.add('description', trv_type)
            e.add('uid', str(uuid.uuid4()))
            e.add('summary', trv_type)
            e.add('dtstart', datetime(int(start_year), int(start[1]), int(start[0])).date())
            e.add('dtend', datetime(int(year), int(end[1]), int(end[0])).date())
            e.add('dtstamp', datetime.now())

            c.add_component(e)

    return Response(c.to_ical(), mimetype='text/calendar')
