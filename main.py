#!/usr/bin/python
# -*- coding: utf-8 -*-

import uuid
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from flask_caching import Cache
from flask import Flask, Response, request
from icalendar import Calendar, Event, Alarm


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
        class_data = table_row["class"]

        year = class_data[0].replace('year-', '')
        week_type = None

        if len(class_data) > 1:
            week_type = class_data[1]

        cells = table_row.findAll('td')

        if len(cells) > 0:

            dates = cells[2].text.split(' - ')
            week = cells[0].text.strip()
            trv_type = cells[1].text.strip()

            start = dates[0].split('.')
            end = dates[1].split('.')

            start_year = int(year)
            start_month = int(start[1])
            start_day = int(start[0])

            end_year = int(year)
            end_month = int(end[1])
            end_day = int(end[0])

            # we need to check if start month is end of year and end month is start of year
            # if this is the case we need to add a year to end_year
            # this happends when end month is on a new year
            if start_month == 12 and end_month == 1:
                end_year += 1

            e = Event()
            e.add('description', trv_type)
            e.add('uid', str(uuid.uuid4()))
            e.add('summary', trv_type)
            e.add('dtstart', datetime(start_year, start_month, start_day).date())
            e.add('dtend', datetime(end_year, end_month, end_day).date() - timedelta(days=1))
            e.add('dtstamp', datetime.now())

            if week_type == 'tommefri-uke':
                desc = 'Avfall tømmes ikke kommende uke.'
            else:
                desc = 'Kommende uke tømmes {0}.'.format(trv_type.lower())

            a = Alarm()
            a.add('action', 'display')
            a.add('trigger', datetime(start_year, start_month, start_day) - timedelta(hours=4))
            a.add('description', desc)
            e.add_component(a)

            c.add_component(e)

    return Response(c.to_ical(), mimetype='text/calendar')
