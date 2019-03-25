import json
import os
from dateutil import parser
import datetime
import string

from collections import Counter


from flask import Flask, jsonify, abort, flash, make_response, render_template, redirect, request, url_for

from flask_login import login_user, logout_user, current_user, login_required
#from flask_login import LoginManager

from werkzeug.urls import url_parse

from app import app, THISDB, APPNAME

from app.utils import get_elevations #, get_external_elevations, getpostcode, check_url_status, save_elevations
from app.forms import LoginForm
#from app.config import Config

import app.parkrun as PARK
import app.parkcharts as parkcharts
import app.geo as geo
from app.db import DBO

from app.models import User

@app.context_processor
def utility_processor():
	def hr():
		if current_user.is_authenticated:
			return current_user.home_run
		else:
			return 'not logged in'
	def hpc():
		if current_user.is_authenticated:
			return current_user.home_postcode
		else:
			return ''
	
	return dict(home_run=hr, home_postcode=hpc)
    
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
	return redirect('/error/')

@app.route('/error/')
def error():
	return render_template('error.html', form=None)

@app.route('/')
def index():
	return redirect('/home/')
	
@app.route('/login/', methods=['POST','GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    HOME_RUN = None
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)

    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/map')
def gmap():
	api_key = open('resources/gmap.key').read()[:-1]
	centre = '{lat: 51.386539, lng: 0.022874}'
	centre = [(51.410992, -0.335791)]
	h = current_user.home_run if current_user.is_authenticated else 'Bromley'
	
	data = geo.closest_runs(h, top=10)
	markers = [list(d.values()) for d in data]
	return render_template('map.html', 
						api_key=api_key, 
						markers=markers,
						map_centre = centre)
	
@app.route('/home/')
@app.route('/home/<name>')
def home(name=None):
	if current_user.is_authenticated:
		closest = geo.closest_runs(current_user.home_run, top=20) 
	else: 
		closest = []
		
	return render_template('home.html', appname=APPNAME, env_home_run=HOME_RUN,
							name=name,
							runners=runners,
							closest=closest,
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
@login_required
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
							    appname=APPNAME, env_home_run=HOME_RUN,
								title = rdtitle[runnerid],
								data = rdtotals[runnerid][page],
								datacount = '(' + str(len(rdtotals[runnerid][page])) + ')' if page != 'missing' else '',
								aggregrate = request.path,
								page = page,
								parent_route = parent_route,
								runnerid = runnerid)
	else:
		return render_template('parkrun.html',
							    appname=APPNAME, env_home_run=HOME_RUN,
								data = pgdata,
								runnerid = runnerid,
								title = rdtitle[runnerid],
								threshold = threshold,
								runners = runners)

@app.route('/runner/')
def runner(id=None):
	print('**', request.path)
	with mydb:
			pgdata = mydb.dcur.execute('select * from runner where public_flag = ' + 
					str(public_flag) + ' order by rid').fetchall()
			pgtitle = 'All Runners'
			
	return render_template('runner.html',
						    appname=APPNAME, env_home_run=HOME_RUN,
							data=pgdata,
							title=pgtitle,
							runners=runners,
							totals={'total': 'TEST', 'year': 2019 })

@app.route('/ele/', methods=['POST','GET'])
#@app.route('/ele/<run>')
def elevation(run=None):
	if request.method.upper() == 'POST':
		data = get_elevations(mydb, request.form['filter'])
	else:
		data = get_elevations(mydb, None)

	return render_template('elevation.html', 
							appname=APPNAME, env_home_run=HOME_RUN,
							data=data, 
							count=len(data), 
							runners=runners)


def runapp(port,debug=True):
	#port = int(os.environ.get("PORT", 80))
	
	app.run(host='0.0.0.0') #app.run(port=port, debug=debug)
	

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


	LOCAL_DATA = os.path.join(os.environ['HOME'] )
	HOME_RUN = 'DEFAULT'

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
#		print('\n** {} completed {} \'A-Z\' letters. Still to complete {}\n\t {}'.
#					format(runner['fullname'], len(az_done), len(missing), missing))
					
		rdtotals[runner['rid']] = {}
		for total_type in {'year', 'month', 'minute', 'course', 'az'}:
			rdtotals[runner['rid']][total_type] = count_by(rd[runner['rid']], total_type)
			#for t in sorted(rdtotals[runner['rid']][total_type],reverse=True):
			#	print(t, rdtotals[runner['rid']][total_type][t])
#		print('***', {l for l in string.ascii_uppercase if l not in az_done.keys()})
		rdtotals[runner['rid']]['missing'] = {'\n'.join(missing): len(missing)}

	chart_data = {'Ian':  rdtotals['184594']['year'],
				  'Matt': rdtotals['185368']['year']}

	parkcharts.makechart(chart_data, './static/mygraph.png', show=False)
	
					
	port = int(os.environ.get("RR_PORT", 8000))

	runapp(port,True)

