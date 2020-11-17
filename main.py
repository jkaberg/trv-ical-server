#!/usr/bin/python
# -*- coding: utf-8 -*-

import uuid
import requests
from datetime import datetime, timedelta
from flask import Flask, Response, request
from icalendar import Calendar, Event, Alarm


app = Flask(__name__)


@app.route('/')
def hello():
    return 'usage: {0}*plan_id*.ics<br /><br />for plan_id see: https://trv.no > search > its the latter part of the url (numeric)'.format(request.base_url)


@app.route('/<plan_id>.ics')
def fetch_plan(plan_id):
    wd = request.args.get('wd', default=None, type=int)
    lang = request.args.get('lang', default='no', type=str)
    alert = request.args.get('alert', default=True, type=bool)

    page = requests.get('https://trv.no/wp-json/wasteplan/v1/calendar/{0}'.format(plan_id))

    if page.json():
        try:
            r = page.json()

            if r.get('data'):
                if r.get('data').get('status') == 404:
                    return Response('404 - not found')

        except ValueError() as e:
            return Response(e)


    c = Calendar()
    c.add('X-WR-RELCALID', 'TRV Tømmeplan')
    c.add('X-WR-CALNAME', 'TRV Tømmeplan')
    c.add('X-WR-TIMEZONE', 'Europe/Oslo')
    c.add('X-FROM-URL', '{0}'.format(request.base_url))
    c.add('X-AUTHOR', 'https://github.com/jkaberg/trv-ical-server')

    for week in r['calendar']:

        # default til norwegian language
        wastetype = week['wastetype'].lower()
        empty_msg = 'Kommende uke tømmes {0}.'.format(wastetype)
        no_empty_msg = 'Avfall tømmes ikke denne uke.'

        # language override
        if lang  == 'en':
            wastetype = week['wastetype_en'].lower()
            empty_msg = 'This week the {0}bin is emptied.'.format(wastetype)
            no_empty_msg = 'Wastebins will not be emptied this week.'

        title = '{0}'.format(wastetype.capitalize())
        summary = title #'\n'.join(list(week['description'])[0].keys()[lang]) # TODO: actully parse this and present it in the summary

        date_week_start = datetime.strptime(week['date_week_start'], '%Y-%m-%d')
        date_week_end = datetime.strptime(week['date_week_end'], '%Y-%m-%d') - timedelta(days=2) # timedelta: remove saturday and sunday

        # limit calendar event til a singel day instead of week with wd paramter
        # monday til friday
        if wd in range(0, 4):
            date_week_start = date_week_start + timedelta(days=wd)
            date_week_end = date_week_start + timedelta(days=1)

            empty_msg = 'Imorgen tømmes {0}.'.format(wastetype)
            if lang == 'en':
                empty_msg = 'Tomorrow the {0}bin is emptied.'.format(wastetype)
        
        e = Event()
        e.add('description', title)
        e.add('uid', str(uuid.uuid4()))
        e.add('summary', summary)
        e.add('dtstart', date_week_start)
        e.add('dtend', date_week_end)
        e.add('dtstamp', datetime.now())

        if alert:
            a = Alarm()
            a.add('action', 'display')
            a.add('trigger', date_week_start - timedelta(hours=4))
            a.add('description', empty_msg if week.get('description') else no_empty_msg)
            e.add_component(a)

        c.add_component(e)

    return Response(c.to_ical(), mimetype='text/calendar')
