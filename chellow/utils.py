from dateutil.relativedelta import relativedelta
from werkzeug.exceptions import BadRequest
import pytz
from decimal import Decimal
import collections
from datetime import datetime as Datetime
from flask import request, Response
from jinja2 import Environment
import time
import traceback


clogs = collections.deque()


def clog(msg):
    clogs.appendleft(
        Datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S") + " - " +
        str(msg))
    if len(clogs) > 1000:
        clogs.pop()


HH = relativedelta(minutes=30)


def req_str(name):
    try:
        return request.values[name]
    except KeyError:
        raise BadRequest("The field " + name + " is required.")


def req_bool(name):
    try:
        return request.values[name] == 'true'
    except KeyError:
        return False


def req_int(name):
    try:
        return int(req_str(name))
    except ValueError as e:
        raise BadRequest(
            "Problem parsing the field " + name + " as an integer: " + str(e))


def req_date(prefix):
    return Datetime(
        req_int(prefix + '_year'), req_int(prefix + '_month'),
        req_int(prefix + '_day'), req_int(prefix + '_hour'),
        req_int(prefix + '_minute'), tzinfo=pytz.utc)


def req_decimal(name):
    return Decimal(req_str(name))


def prev_hh(dt):
    return None if dt is None else dt - HH


def next_hh(dt):
    return None if dt is None else dt + HH


def hh_after(dt1, dt2):
    if dt2 is None:
        return False
    else:
        return True if dt1 is None else dt1 > dt2


def hh_before(dt1, dt2):
    if dt1 is None:
        return False
    else:
        return True if dt2 is None else dt1 < dt2


def get_contract_func(contract, func_name):
    gb = {}
    exec(contract.charge_script, gb)
    return gb.get(func_name)


def req_hh_date(prefix):
    dt = req_date(prefix)
    validate_hh_start(dt)
    return dt


def validate_hh_start(dt):
    if dt.minute not in [0, 30] or dt.second != 0 or dt.microsecond != 0:
        raise BadRequest(
            "The half-hour must start exactly on the hour or half past "
            "the hour.")
    return dt


def parse_hh_start(start_date_str):
    if len(start_date_str) == 0:
        return None

    try:
        year = int(start_date_str[:4])
        month = int(start_date_str[5:7])
        day = int(start_date_str[8:10])
        hour = int(start_date_str[11:13])
        minute = int(start_date_str[14:])
        return validate_hh_start(
            Datetime(year, month, day, hour, minute, tzinfo=pytz.utc))
    except ValueError as e:
        raise BadRequest(
            "Can't parse the date: " + start_date_str +
            ". It needs to be of the form yyyy-mm-dd hh:MM. " + str(e))


def parse_mpan_core(mcore):
    mcore = mcore.strip().replace(' ', '')
    if len(mcore) != 13:
        raise BadRequest(
            "The MPAN core '" + mcore + "' must contain exactly 13 digits.")

    for char in mcore:
        if char not in '0123456789':
            raise BadRequest(
                "Each character of an MPAN must be a digit.")

    ps = [3, 5, 7, 13, 17, 19, 23, 29, 31, 37, 41, 43]
    cd = sum(p * int(d) for p, d in zip(ps, mcore[:-1])) % 11 % 10
    if cd != int(mcore[-1]):
        raise BadRequest(
            "The MPAN core " + mcore +
            " is not valid. It fails the checksum test.")

    return ' '.join([mcore[:2], mcore[2:6], mcore[6:10], mcore[10:]])


def parse_bool(bool_str):
    return bool_str.lower() == 'true'


def hh_format(dt):
    return 'ongoing' if dt is None else dt.strftime("%Y-%m-%d %H:%M")


CHANNEL_TYPES = 'ACTIVE', 'REACTIVE_IMP', 'REACTIVE_EXP'


def parse_channel_type(channel_type):
    tp = channel_type.upper()
    if tp not in CHANNEL_TYPES:
        raise BadRequest(
            "The given channel type is '" + str(channel_type) +
            "' but it should be one of " + str(CHANNEL_TYPES) + ".")
    return tp


def parse_pc_code(code):
    return str(int(code)).zfill(2)


def send_response(
        content, args=None, status=200, content_type='text/csv; charset=utf-8',
        file_name=None):
    headers = {}
    if args is None:
        args = ()

    if file_name is not None:
        headers['Content-Disposition'] = 'attachment; filename="' + \
            file_name + '"'

    return Response(
        content(*args), status=status, content_type=content_type,
        headers=headers)


FORMATS = {
    'year': '%Y', 'month': '%m', 'day': '%d', 'hour': '%H',
    'minute': '%M', 'full': '%Y-%m-%d %H:%M', 'date': '%Y-%m-%d'}

prefix = '''
{%- macro input_date(prefix, initial=None, resolution='minute') -%}
  {% if prefix != None %}
    {% set year_field = prefix + '_year' %}
    {% set month_field = prefix + '_month' %}
    {% set day_field = prefix + '_day' %}
    {% set hour_field = prefix + '_hour' %}
    {% set minute_field = prefix + '_minute' %}
  {% else %}
    {% set year_field = 'year' %}
    {% set month_field = 'month' %}
    {% set day_field = 'day' %}
    {% set hour_field = 'hour' %}
    {% set minute_field = 'minute' %}
  {% endif %}

  {% set initial = initial|now_if_none %}

  <input name="{{ year_field }}" maxlength="4" size="4" value="
    {%- if request.values.year_field -%}
      {{ request.values.year_field }}
    {%- else -%}
      {{ initial|hh_format('year') }}
    {%- endif %}">

  {%- if resolution in ['month', 'day', 'hour', 'minute'] -%}
    -<select name="{{ month_field }}">
    {% for month in range(1, 13) -%}
      <option value="{{ "%02i"|format(month) }}"
        {%- if request.values.month_field -%}
          {%- if request.values.month_field|int == month %} selected
          {%- endif -%}
        {%- else -%}
          {%- if initial.month == month %} selected{%- endif -%}
        {%- endif -%}>{{ "%02i"|format(month) }}</option>
    {% endfor %}
    </select>
  {%- endif -%}

  {% if resolution in ['day', 'hour', 'minute'] -%}
    -<select name="{{ day_field }}">
      {% for day in range(1, 32) -%}
        <option value="{{ day }}"
          {%- if request.values.day_field -%}
            {%- if request.values.day_field|int == day %} selected
            {% endif -%}
          {% else %}
            {%- if initial.day == day %} selected{% endif -%}
          {%- endif %}>{{ "%02i"|format(day) }}</option>
      {% endfor -%}
    </select>
  {%- endif -%}

  {% if resolution in ['hour', 'minute'] %}
    <select name="{{ hour_field }}">
      {% for hour in range(24) %}
        <option value="{{ hour }}"
          {%- if request.values.hour_field -%}
            {%- if request.values.hour_field|int == hour %} selected
            {%- endif -%}
          {%- else -%}
            {%- if initial.hour == hour %} selected{%- endif -%}
          {%- endif %}>{{ "%02i"|format(hour) }}</option>
      {%- endfor %}
    </select>
  {%- endif -%}

  {% if resolution == 'minute' -%}
    :<select name="{{ minute_field }}">
      {% for minute in range(0, 31, 30) -%}
        <option value="{{ minute }}"
          {%- if request.values.minute_field %}
            {%- if request.values.minute_field|int == minute %} selected
            {%- endif %}
          {%- else %}
            {%- if initial.minute == minute %} selected{% endif %}
            {%- endif %}>{{ "%02i"|format(minute) }}</option>
      {% endfor %}
    </select>
  {%- endif %}
{%- endmacro -%}

{%- macro input_option(name, item_id, desc, initial=None) -%}
    <option value="{{ item_id }}"
        {%- if request.values.name -%}
            {%- if request.values.name == '' ~ item_id %} selected
            {%- endif -%}
        {%- else -%}
            {%- if initial == item_id %} selected{% endif -%}
            {%- endif -%}>{{ desc }}</option>
{%- endmacro -%}

{% macro input_text(name, initial=None, size=None, maxlength=None) %}
    <input name="{{ name }}" value="
        {%- if request.values.name -%}
            {{ request.values.name }}
        {%- elif initial is not none -%}
            {{initial}}
        {%- endif -%}"
        {%- if size %} size="{{ size }}"{% endif %}
        {%- if maxlength %} maxlength="{{ maxlength }}"{% endif %}>
{%- endmacro -%}

{% macro input_textarea(name, initial, rows, cols) -%}
  <textarea name="{{ name }}" rows="{{ rows }}" cols="{{ cols }}">
    {%- if request.values.name -%}
      {{ request.values.name }}
    {%- else -%}
      {{ initial }}
    {%- endif -%}
  </textarea>
{%- endmacro -%}

{%- macro input_checkbox(name, initial) %}
    <input type="checkbox" name="{{ name }}" value="true"
                {%- if request.values.name -%}
                    {%- if request.values.name == 'true' %} checked
                    {%- endif -%}
                {%- else -%}
                    {%- if initial == True %} checked{% endif -%}
                    {%- endif -%}>
{%- endmacro -%}
'''


def hh_format_filter(dt, modifier='full'):
    return "Ongoing" if dt is None else dt.strftime(FORMATS[modifier])


def now_if_none(dt):
    return Datetime.utcnow() if dt is None else dt


env = Environment(autoescape=True)

env.filters['hh_format'] = hh_format_filter
env.filters['now_if_none'] = now_if_none

template_cache = {}


def render(template, vals, status_code=200, content_type='text/html'):
    if len(template_cache) > 10000:
        template_cache.clear()
    templ_str = prefix + template
    try:
        templ = template_cache[templ_str]
    except KeyError:
        templ = env.from_string(templ_str)
        template_cache[templ_str] = templ

    vals['request'] = request

    headers = {
        'mimetype': content_type,
        'Date': int(round(time.time() * 1000)),
        'Cache-Control': 'no-cache'}

    try:
        template_str = templ.render(vals)
    except:
        raise BadRequest(
            "Problem rendering template: " + traceback.format_exc())

    return Response(template_str, status_code, headers)
