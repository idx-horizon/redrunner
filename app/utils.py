
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import httplib2
import re

def check_url_status(url,app):
    headers = {
        'User-Agent': app.config['USER_AGENT']
    }
    h = httplib2.Http()
    resp = h.request(url, 'HEAD', headers=headers)
    return resp[0]['status']


def getpostcode(course,app):
    url = 'http://www.parkrun.org.uk/' + course + '/course/'
    headers = {
        'User-Agent': app.config['USER_AGENT']
    }
    html = urlopen(Request(url, headers=headers))
    soup = BeautifulSoup(html, 'html5lib')

    pcs = re.findall("[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}", soup.text)
    return (course, len(pcs), pcs, soup)


def get_external_elevations(app):
    url = 'https://jegmar.com/stats-hq/fastest-races/parkrun'
    print('** Getting external data')
    html = urlopen(url,app)

    soup = BeautifulSoup(html, 'html5lib')

    tr = soup.find_all('tr')

    runs = []

    id = 0
    for row in tr:  # [0:10]:
        line = ''
        for cell in row.find_all(['th', 'td'], class_=['column-1', 'column-2', 'column-4']):
            line = line + ',' + cell.get_text().strip()
        elements = line[1:].split(',')

        url = 'http://www.parkrun.org.uk/' + elements[1].lower().replace(' ', '') + '/course/'
        url_status = check_url_status(url)
        print(url_status, url)
        runs.append({'id': id,
                     'pos': elements[0],
                     'run': elements[1],
                     'elevation': elements[2],
                     'url': elements[1].lower().replace(' ', ''),
                     'url_status': url_status
                     })
        id += 1

    return runs[1:]


def get_elevations(filter=None):
    with mydb:
        data = json.loads(mydb.dcur.execute('select * from reference where key=\'elevations\'').fetchall()[0]['value'])
        if filter:
            data = [selected for selected in data if filter.lower() in selected['run'].lower()]

        return data


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

    print('Saved %s elevation records' % (len(runs, )))
