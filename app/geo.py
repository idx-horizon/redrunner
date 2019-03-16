import urllib.request
import requests
import json
import xml.etree.ElementTree as ET
from pprint import pprint
from math import sin, cos, sqrt, atan2, radians


def get_postcode_coordinates(postcode):
	api = 'https://api.postcodes.io/postcodes/'
	response = requests.get(api + postcode)
	if response:
		result = response.json()['result']
		return (result['latitude'], result['longitude'])
	else:
		print('Error: not found {}'.format(postcode))	
	
	
def get_coordinates(place, root):
	for e in root.findall('.//e/[@m="' + place + '"]'):
		try: 
			return ( float(e.get('la')), float(e.get('lo')))		
		except:
			pass
					
	return (0,0)
	
def measure(from_loc, to_loc):
	EARTH_RADIUS = 6373

	lat1 = radians(from_loc[0]) 
	lon1 = radians(from_loc[1])   
	lat2 = radians(to_loc[0]) 
	lon2 = radians(to_loc[1]) 
	
	dlon = lon2 - lon1
	dlat = lat2 - lat1
	
	a = sin(dlat /2)**2 + cos(lat1) * cos(lat2) * sin(dlon /2)**2
	c = 2 * atan2(sqrt(a), sqrt(1-a))
	
	distance = (EARTH_RADIUS * c) *5/8
	
	return distance
	
def closest_runs(run=None, postcode=None, top=10):
	tree = ET.parse('geo.xml')
	root = tree.getroot()

	dist = {}		
	if run:
		from_name = 'Parkrun: ' + run
		from_coord = get_coordinates(run, root)
		offset = 1
	elif postcode:
		from_name = 'Postcode: ' + postcode
		from_coord = get_postcode_coordinates(postcode)
		offset = 0
	else:
		print('ERROR: must supply either run or postcode')
		return
		
	print('\nClosest {} runs from {} {}'.format(top, from_name, from_coord))
	for m in tree.iter('e'):
		p = m.get('m')
		la, lo = get_coordinates(p,root)
		try:
			dist[p] =  measure(from_loc=from_coord, to_loc=(float(la), float(lo)))
		except:
			pass
				
	top_list = sorted(dist, key=dist.get)[:top+offset]
		
	for ix, w in enumerate(top_list[offset:]):
		print('{:>3}. {:<30} distance {:.2f} (m)'.format(ix+1, w, dist[w]))
	
	return top_list[offset:]
	
#closest_runs(run='Bromley',top=10)
#closest_runs(postcode='BR4 9NY',top=20)
#closest_runs(postcode='CR5 3AL',top=20)

#closest_runs(run='Banstead Woods',top=10)