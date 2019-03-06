import console
import requests
import pprint as pp
import re
import os
import json
import time
import datetime
import app.db
import bs4					

def extract_tables(html_text):
	table_pattern = r'(<table[^>]*>(?:.|\n)*?<\/table>)' 
	header_pattern = r'(<th[^e/]*>(?:.|\n)*?<\/th>)'
	caption_pattern = r'<caption>*>(?:.|\n)*?<\/caption>'
	td_pattern = r'<td>*>(?:.|\n)*?<\/td>'
	h2_pattern = r'<h2>*>(?:.|\n)*?<\/h2>'
	remove_tag_pattern = r'<[^>]*>'

	tables = re.findall(table_pattern, html_text)
	response = {}
	table_count = 0
	
	h2 = re.findall(h2_pattern, html_text)
	if h2:
		h2name = re.sub(remove_tag_pattern,'', h2[0].replace('<br/>',' ')).replace('\n',' ')
	else:
		h2name = 'Unknown'
	
	for t in tables[0:3]:
		table_count += 1
		captions = re.findall(caption_pattern,t)
		if captions:
			caption = re.sub(remove_tag_pattern,'', captions[0])
		else:
			caption = str(table_count) + '. Table'
			
		headers = [re.sub(remove_tag_pattern,'',h) for h in re.findall(header_pattern, t)]
		for e in re.findall(r'<th\/>', t):
			headers.insert(0,'')
			
		i = 1
		data = [re.sub(remove_tag_pattern,'',d).strip() for d in re.findall(td_pattern,t)]

		response[str(table_count)] = {'headers': headers,
									'number_cols': len(headers),
									'data_count': len(data),
									'data': data,
									'caption': caption,
									'title': h2name}
	return response

def get_chunk_as_tuples(datalist, n):
    """Yield successive n-sized chunks as tuple from datalist"""
    for i in range(0, len(datalist), n):
        yield tuple(datalist[i:i + n])
		
def run(runner, LOCAL_DATA, mydb=None):

	runner_datafile = os.path.join(LOCAL_DATA, runner + '.txt')	
	if os.path.exists(runner_datafile):
		with open(runner_datafile,'r') as fh:
			b = json.load(fh)
		return b, b['1']['title'].strip() +' (local)'
#		return b, b['1']['title'].strip() +' (local)', None
	else:
		print('No local data for runner', runner, '- getting data from website')
		
	link ='http://www.parkrun.org.uk/results/athleteeventresultshistory/?athleteNumber=' + runner + '&eventNumber=0'

	headers  =  {
		'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36'
		}	

#	print(link)

	session = requests.Session()
	session.headers.update(headers)
	sr = session.get(link)
#	print('Response from get: ', sr.status_code, 'Length of response:', len(sr.text), '\n')			
	b  = extract_tables(sr.text)
	
	for t in b:
		cols = b[t]['number_cols']
		rows = int(b[t]['data_count'] / cols)
#		max_width = len(max(b[t]['data'],key=len)) + 2
#		output_format = '{:<' + str(max_width) + '}'
#		
#		print('Table:', b[t]['caption'], b[t]['headers'], 'Columns:', cols, 'Rows:', rows)
#		line = ''
#		for h in b[t]['headers']:
#			line += output_format.format(h)
#		print(line)
#		
#		for i in range(0,rows):			
#			line = ''		
#			for d in b[t]['data'][cols*i : (cols*i)+cols]: 
#				line += output_format.format(d)
#			#print(b[t]['data'][cols*i : (cols*i)+cols])
#			#print(line)
#		print('\n')
	
		b[t]['rowdata'] =[]
		for i in get_chunk_as_tuples(b[t]['data'],b[t]['number_cols']):
			b[t]['rowdata'].append(i)
	
	with open(os.path.join(LOCAL_DATA, runner + '.txt'),'w') as fh:
		json.dump(b, fh)
		time.sleep(1)
		saverunner(b, runner, mydb)
		
	return b,b['1']['title']

def saverunner(data, runnerid, mydb):
#	print('start save to db')
	with mydb:
		print('** Saving {} into reference'.format(runnerid))
		store_data = json.dumps(data)
		mydb.cur.execute('delete from reference where key=? and subkey=?',
										 ('runner', runnerid))
		mydb.cur.execute('INSERT into reference values (?,?,?,?)', 
											('runner', 
											  runnerid, 
											  store_data, 
											  datetime.datetime.now()))
		mydb.conn.commit()


if __name__ == '__main__':

	current_runner = 0
	runners = ['184594', '185368', '4327482']
	#print(os.getcwd(), os.environ['HOME'])
	
	#LOCAL_DATA = os.path.join(os.environ['HOME'], 'Documents/_DATA')
	LOCAL_DATA = os.path.join('/private/var/mobile/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents', '_DATA')
	print(LOCAL_DATA)
	data, title, sr = run(runners[current_runner], LOCAL_DATA)
	data, title,sr = run(runners[current_runner], LOCAL_DATA)
		
	if data:
		MyVw(data, title)
		pass
	

