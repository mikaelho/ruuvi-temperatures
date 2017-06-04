# coding: utf-8
import os
import requests
import codecs
import datetime
import pygal
from pygal.style import Style, NeonStyle, LightGreenStyle, CleanStyle, LightColorizedStyle

import pytz
tz = pytz.timezone('Europe/Helsinki')

# Get PubNub subscribe key for the temperature data
with open('subscribe-key.txt') as key_file:
  sub_key = key_file.read().strip()

def handler(event = None, context = None):
  """
  @awslambda @html
  """
  
  result = requests.request('GET', 'https://ps.pndsn.com/v2/history/sub-key/'+sub_key+'/channel/dasher?count=36')
  
  sensors = {}
  times = []
  
  for message in result.json()[0]:
    if message['appID'] == 'ruuvi':
      timestamp = message['timestamp']
      times.append(timestamp)
      for (location, temp) in message['temperatures']:
        sensors.setdefault(location, {})
        sensors[location][timestamp] = int(temp)
        
  times = sorted(times)
  
  chart = pygal.Line(
    #style=LightColorizedStyle,
    #fill=True,
    #x_label_rotation=20,
    #print_values=True,
    #print_values_position='top',
    #dynamic_print_values=True,
    interpolate='hermite', interpolation_parameters={
      'type': 'kochanek_bartels',
      'b': -1, 'c': 1, 't': 1
    },
    legend_at_bottom=True, legend_at_bottom_columns=len(sensors),
    style = Style(
      label_font_size=14,
      major_label_font_size=24,
      legend_font_family='monospace',
      legend_font_size=28
    )
  )
  
  time_labels = []
  previous = 0
  for timestamp in times:
    dt = datetime.datetime.fromtimestamp(timestamp, tz)
    if dt.day != previous:
      previous = dt.day
      time_labels.append('|')
    else:
      time_labels.append(dt.strftime('%H'))
  chart.x_labels = time_labels
  chart.x_labels_major = ['00']
  
  result_html = ''
  
  active_sensor_count = 0
  last_temps = []
  for location in sensors:
    readings = sensors[location]
    temps = []
    for timestamp in times:
      temps.append(readings.get(timestamp, None))
    chart.add(
      location, temps,
      allow_interruptions=True,
      stroke_style={'width': 5}
    )
    if temps[-1] is not None:
      last_temps.append((location, temps[-1]))
      active_sensor_count += 1
      
  last_temps = sorted(last_temps, key=lambda reading: reading[1], reverse=True)
  
  for (location, temp) in last_temps:
    if result_html != '':
      result_html += '<br/><br/>'
    result_html += '<span style="font-size: 40px; font-weight: bold">' + str(temp) + ' &deg;C</span><br/>' + location
  
  with codecs.open('main.html', encoding='utf-8') as file_in:
    main_html = file_in.read()
  return main_html % {
    #'sensor_count': active_sensor_count,
    'main_content': result_html,
    'chart_content': chart.render_data_uri()
  }

if __name__ == '__main__':
  import ui
  v = ui.WebView()
  html_content = handler({'queryParams': {'name': 'world'}})
  v.load_html(html_content)
  v.present()

