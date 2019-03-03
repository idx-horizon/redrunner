import webbrowser
import json
import os
import pprint as pp
import console
from dateutil import parser
import datetime
import re
import string

from collections import Counter

from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import httplib2

from flask import Flask, jsonify, abort, make_response, render_template, redirect, request

import src.parkrun as PARK
import src.parkcharts as parkcharts
from src.db import DBO 

app = Flask(__name__)


@app.template_filter()
def datetimefilter(value, format='%d-%b-%Y'):

	"""convert a datetime to a different format."""
	try:
		dt = parser.parse(value, dayfirst=True)
		response = dt.strftime(format)
	except:
		response = value
	return response
	
app.jinja_env.filters['datetimefilter'] = datetimefilter
		
@app.errorhandler(404)
def error_404(error):
	return make_response(jsonify({'error': '404 - Not found'}), 404)
	
	
@app.errorhandler(500)
def handle_error_route(error):
	return make_response(jsonify({'error': '500 - Internal application error'}), 500)
	
@app.route('/')
def index():
	return redirect('/home/')
	
	
@app.route('/home/')
@app.route('/home/<name>')
def home(name=None):
	return render_template('home.html', 
													name=name, 
													runners=runners, 
													timestamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
	
@app.route('/parkrun/', methods=['POST','GET'])
@app.route('/parkrun/<id>/', methods=['POST','GET'])
@app.route('/parkrun/<id>/totals', methods=['POST','GET'])
@app.route('/parkrun/<id>/az', methods=['POST','GET'])
@app.route('/parkrun/<id>/course', methods=['POST','GET'])
@app.route('/parkrun/<id>/minute', methods=['POST','GET'])
@app.route('/parkrun/<id>/year', methods=['POST','GET'])
@app.route('/parkrun/<id>/month', methods=['POST','GET'])
@app.route('/parkrun/<id>/missing', methods=['POST','GET'])
def parkrun(id=None):
	print('**', request.path, request.path.split('/')[-1])		

	if id:
		runnerid = id
		threshold = [r['threshold'] for r in runners if r['rid'] == id][0]
		pgdata = rd[id]
		if request.method.upper() == 'POST':
			pgdata = [selected for selected in rd[id] if request.form['filter'].lower() in selected['Event'].lower()]		
		else:
			pgdata = rd[id]		
	else:
		runnerid = runners[0]['rid']
		threshold = runners[0]['threshold']
		pgdata = rd[runnerid]			
	
	if request.path.split('/')[-1] in {'az', 'year', 'month', 'minute', 'course', 'missing'}:
		page = request.path.split('/')[-1]
		parent_route = request.path.replace('/'+page, '')
		
		return render_template('totals.html',
								title = rdtitle[runnerid],
								data = rdtotals[runnerid][page],
								datacount = '(' + str(len(rdtotals[runnerid][page])) + ')' if page != 'missing' else '',
								aggregrate = request.path,
								page = page,
								parent_route = parent_route,
								runnerid = runnerid)
	else:
		return render_template('parkrun.html',
								data = pgdata,
								runnerid = runnerid,
								title = rdtitle[runnerid],
								threshold = threshold,
								runners = runners)

@app.route('/runner/')
def runner(id=None):
	print('**', request.path)
	with mydb:
			pgdata = mydb.dcur.execute('select * from runner where public_flag = ' + str(public_flag) + ' order by rid').fetchall()
			pgtitle = 'All Runners'
			
	return render_template('runner.html',
							data=pgdata,
							title=pgtitle,
							runners=runners,
							totals={'total': 'TEST', 'year': 2019 })

@app.route('/ele/', methods=['POST','GET'])
#@app.route('/ele/<run>')
def elevation(run=None):
	if request.method.upper() == 'POST':
#		run = request.form['filter']
		data = get_elevations(request.form['filter'])
	else:
		data = get_elevations(None)

	return render_template('elevation.html', data=data, count=len(data), runners=runners)
			
def test():
	console.clear()
	mydb = DBO(THISDB)
	with mydb:
		for sql in {'select * from todo where status = 1',
		'select * from sqlite_master',
		'select * from reference',
		'select * from person',
		'select * from elevation'}:
			r = mydb.getdata(sql)
			print('\n** Executing: %s' % (sql,))
			for member in r:
				for k in member.keys():
					print(k, '=' , member[k])
			#pp.pprint(r)
			print('** Result count:',len(r), '\n')
			
		print('**Tables with columns')
		for tbl in mydb.cur.execute('select name from sqlite_master where type = \'table\'').fetchall():
			mydb.cur.execute('select * from ' + tbl[0] + ' where 1=0').fetchall()
			
			cols = next(zip(*mydb.cur.description))
			print('* Table %s: Columns: %s' % (tbl[0], cols))

def check_url_status(url):
	headers  =  {
			'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36'
	}		
	h = httplib2.Http()
	resp = h.request(url, 'HEAD', headers=headers)
	return resp[0]['status']

def getpostcode(course):
		url = 'http://www.parkrun.org.uk/' + course + '/course/'
		headers  =  {
			'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36'
		}	
		html = urlopen(Request(url, headers=headers))
		soup = BeautifulSoup(html, 'html5lib')
		
		pcs = re.findall("[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}", soup.text)
		return (course, len(pcs), pcs, soup)
		
def get_external_elevations():
	url = 'https://jegmar.com/stats-hq/fastest-races/parkrun'
	print('** Getting external data')
	html = urlopen(url)
	
	soup = BeautifulSoup(html, 'html5lib')
	
	tr = soup.find_all('tr')
	
	runs =[]
	
	id = 0
	for row in tr: #[0:10]:
		line = ''
		for cell in row.find_all(['th','td'],class_=['column-1','column-2', 'column-4']):
			line = line + ',' + cell.get_text().strip()
		elements = line[1:].split(',')
		
		url = 'http://www.parkrun.org.uk/' + elements[1].lower().replace(' ','') + '/course/' 
		url_status = check_url_status(url)
		print(url_status, url)
		runs.append ({'id': id, 
									'pos': elements[0], 
									'run': elements[1], 
									'elevation': elements[2],
									'url': elements[1].lower().replace(' ',''),
									'url_status': url_status
									})
		id += 1
		
	return runs[1:]

def get_elevations(filter=None):
	with mydb:
		data =  json.loads(mydb.dcur.execute('select * from reference where key=\'elevations\'').fetchall()[0]['value'])
		if filter:
			data = [selected for selected in data if filter.lower() in selected['run'].lower()]
	
		return data
							
def runapp(port,debug=True):
	#port = int(os.environ.get("PORT", 80))
	
	app.run(host='0.0.0.0') #app.run(port=port, debug=debug)
	
def save_elevations():
	runs = get_external_elevations()
	id = 1
	with mydb:
		mydb.cur.execute('delete from reference where key = ?', ('elevations',))
		store_runs = json.dumps(runs)
		mydb.cur.execute('INSERT into reference values (?,?,?,?)', 
											('elevations', 
											  '',
											  store_runs, 
											  datetime.datetime.now()))
		
		mydb.conn.commit()
		
	print('Saved %s elevation records' % (len(runs,)))

def count_by(runner, type='course'):
	#ct = Counter({}.fromkeys(string.ascii_uppercase,0))	
	ct = Counter()
	for e in runner:
		if type == 'course':
			ct[e['Event']] += 1	
		elif type == 'az':
			ct[e['Event'][0].upper()] += 1
		elif type == 'year':
			ct[e['Run Date'][-4:]] += 1
		elif type == 'month':
			ct[e['Run Date'][-4:] + '-' + e['Run Date'][-7:-5] ] += 1
		elif type == 'minute':
			ct['Sub ' + str(int(e['Time'][:2])+1) + ' min'] += 1			
				
	return dict(ct)
		
if __name__ == '__main__':

	THISDB = 'REPOSITORY.db'
	LOCAL_DATA = os.path.join(os.environ['HOME'] )

	public_flag = os.environ['RR_PUBLIC_FLAG']
	mydb = DBO(THISDB)

	with mydb:
		runners = mydb.dcur.execute('select * from runner order by rid').fetchall()

	print('Number of runners: {}'.format(len(runners)))	
	rd = {}
	rdtitle = {}
	rdtotals = {}
	for runner in runners:
		runnerdata, runnertitle = PARK.run(runner['rid'], LOCAL_DATA, mydb)
		h = runnerdata['3']['headers']
		dt = runnerdata['3']['data']
		rd[runner['rid']] = [dict(zip(h,dt[i:i+len(h)])) for i in range(0,len(dt),len(h))]	
		rdtitle[runner['rid']] = runnertitle

		az_done = count_by(rd[runner['rid']], 'az')
		missing = [l for l in string.ascii_uppercase if l not in az_done.keys()]
		print('\n** {} completed {} \'A-Z\' letters. Still to complete {}\n\t {}'.
					format(runner['fullname'], len(az_done), len(missing), missing))
					
		rdtotals[runner['rid']] = {}
		for total_type in {'year', 'month', 'minute', 'course', 'az'}:					
			rdtotals[runner['rid']][total_type] = count_by(rd[runner['rid']], total_type)
			#for t in sorted(rdtotals[runner['rid']][total_type],reverse=True):
			#	print(t, rdtotals[runner['rid']][total_type][t])
		print('***', {l for l in string.ascii_uppercase if l not in az_done.keys()})
		rdtotals[runner['rid']]['missing'] = {'\n'.join(missing): len(missing)}

	chart_data = {'Ian': rdtotals['184594']['year'], 
							#	'Michael': rdtotals['2564629']['year'],
								'Matt': rdtotals['185368']['year']}
	print('Current directory: ', os.getcwd())
	parkcharts.makechart(chart_data, './static/mygraph.png', show=False)
					
	port = int(os.environ.get("PORT", 8000))
#	webbrowser.open('googlechrome://localhost:' + str(port))
#	webbrowser.open('safari-http://localhost:' + str(port))

	runapp(port,True)

