import json
import os
from dateutil import parser
import datetime
import string

from collections import Counter


from flask import Flask, jsonify, abort, flash, make_response, render_template, redirect, request, url_for, session

from flask_login import login_user, logout_user, current_user, login_required

from werkzeug.urls import url_parse

from app import app, THISDB, APPNAME, THISCONFIG

from app.utils import get_elevations
from app.forms import LoginForm
#from app.config import Config

import app.parkrun as PARK
import app.parkcharts as parkcharts
import app.geo as geo
from app.db import DBO

from app.models import User

@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                 endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)
    
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
	return redirect('/error/404')

@app.errorhandler(500)
def handle_error_route(error):
	return redirect('/error/500')

@app.route('/error/')
@app.route('/error/<code>')
def error(code=None):
	return render_template('error.html', error_code=code)

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

@app.route('/home/')
@app.route('/home/<name>')
def home(name=None):
	api_key = open('resources/gmap.key').read()[:-1]
	if current_user.is_authenticated:
		h = current_user.home_run 
		rid = current_user.rid
		runner_data = rd[rid]
	else:
		h = 'Bushy Park'
		rid = None
		runner_data = []
	
	centre = list(geo.get_coordinates(h,None))
		
	data = geo.closest_runs(h, top=50, runner_data=runner_data)
	markers = [list(d.values()) for d in data]
	return render_template('home.html', 
						api_key=api_key, 
						markers=markers,
						map_centre=centre,
						rid=rid)
	
@app.route('/user/')
@app.route('/user/<name>')
def user_route(name=None):
		
	return render_template('user.html',
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
		if current_user.is_authenticated:
			pgtitle = current_user.username + "'s runners"
			sql='''
				select * from runnerlink as L 
				left join runner as R 
					on (L.rid=R.rid) 
				where username = "''' + current_user.username + '"'
		else:
			sql = '''
					SELECT * from runner 
					WHERE 
						public_flag = 1 
					ORDER BY rid;
				'''
			pgtitle = "Public runners"

		pgdata = mydb.dcur.execute(sql).fetchall()
			
	return render_template('runner.html',
						    appname=APPNAME, env_home_run=HOME_RUN,
							data=pgdata,
							title=pgtitle,
							runners=runners,
							sql=sql)

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
	print('** Port: ', port)
	app.run(host='0.0.0.0') #app.run(port=port, debug=debug)
	logout_user()
	

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
					
		rdtotals[runner['rid']] = {}
		for total_type in {'year', 'month', 'minute', 'course', 'az'}:
			rdtotals[runner['rid']][total_type] = count_by(rd[runner['rid']], total_type)
		rdtotals[runner['rid']]['missing'] = {'\n'.join(missing): len(missing)}
	
					
	port = int(os.environ.get("RR_PORT", 8000))

	runapp(port,True)

