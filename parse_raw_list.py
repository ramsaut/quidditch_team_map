#!/usr/bin/env python
import os
import re
import json
from bs4 import BeautifulSoup
from geopy import geocoders

GEOJSON_FILE_NAME = 'geo.json'
RAW_LIST_FILE_NAME = 'raw_teamlist.txt'
GPS_FILE_NAME = 'gps.txt'
FIRST_COUNTRY = 'Austria'

def parse_team_string(s):
    regex = r"^([^\-\–*()]*(?:\([\w\-\–]*\))?[^\-\–*()]*)[\-\– ]*(\*)?[\-\– ]*(.*)$"
    m = re.search(regex, s)
    team = m.group(1).strip()
    recognised = m.group(2) == '*'
    captain = m.group(3).strip()
    return (team, recognised, captain)

def create_feature(team_name, recognised, captain, lat, long):
    return { "type": "Feature",
        "geometry": {
          "type": "Point",
          "coordinates": [lat, long]},
          "properties": {
            "name": team_name,
            "recognised": recognised,
            "captain": captain,
          }
        }


file_name = os.path.join(os.path.dirname(__file__), RAW_LIST_FILE_NAME)
raw_file  = open(file_name, 'r')

soup = BeautifulSoup(raw_file, 'html.parser')
raw_file.close()
main_part = soup.div.contents

found_first_country = False
country_dict = dict()
for child in main_part:
    if not found_first_country:
        if child.string == FIRST_COUNTRY:
            found_first_country = True
        else:
            continue
    if child.name == 'div':
        if child.string:  # There is an empty line before the Netherlands
            s = child.string
            print("Country: " + s)
            if(s.find("Unofficial Teams:")!=-1 or s.find("Unofficial teams:"))!=-1:
                continue
            s = s.replace("Official Teams:","",1)
            current_country = s.strip()
    else:
        team_list = child.contents
        country_dict[current_country] = []
        for team in team_list:
            print("Team: " + team.string)
            country_dict[current_country].append(parse_team_string(team.string))

gps_file_name = os.path.join(os.path.dirname(__file__), GPS_FILE_NAME)
gps_file = open(gps_file_name, 'r')
current_teams = json.loads(gps_file.read())
gps_file.close()
gn = geocoders.Nominatim()

features = []

for country in country_dict:
    teams = country_dict[country]
    print("Country: {}".format(country))
    for team in teams:
        if team[0] not in current_teams:
            apply = 'n'
            while apply == 'n':
                inp = input("{}: ".format(team[0]))
                if not inp:
                    code = None
                    break
                code = gn.geocode("{}, {}".format(inp, country))
                apply = input("{} (Y/n/NA)".format(code))
                if apply == 'NA':
                    code = None
            if code is None:
                continue
            current_teams[team[0]] = (code.latitude, code.longitude)
            gps_file = open(gps_file_name, 'w')
            gps_file.write(json.dumps(current_teams, sort_keys=True,
                                      indent=4, separators=(',', ': ')))
            gps_file.close()

        features.append(create_feature(
            team[0],
            team[1],
            team[2],
            current_teams[team[0]][1],
            current_teams[team[0]][0]))

geojson = {"type": "FeatureCollection",
           "features": features}

geojson_file_name = os.path.join(os.path.dirname(__file__), GEOJSON_FILE_NAME)
geojson_file = open(geojson_file_name, 'w')
geojson_file.write(json.dumps(geojson, sort_keys=True,
                          indent=4, separators=(',', ': ')))
geojson_file.close()