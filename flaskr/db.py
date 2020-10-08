import click
import requests
import time
import os
import psycopg2

from flask import current_app, g
from flask.cli import with_appcontext
from bs4 import BeautifulSoup


def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(os.environ["DATABASE_URL"], sslmode='require')

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()
    cursor = db.cursor()

    with current_app.open_resource('schema.sql') as f:
        cursor.execute(f.read().decode('utf8'))

    # populate servers
    #    url="https://www.dofus.com/fr/mmorpg/communaute/serveurs#jt_list"
    print('Servers')
    servers = {}
    for (i, commu) in [(0,"fr"),(2,"int"),(4,"es"),(6, "port")]:
        url = f"https://www.dofus.com/fr/mmorpg/communaute/serveurs?server_community%5B%5D={i}#jt_list"
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        results = soup.find("table").find("tbody").find_all("tr")
        for elem in results:
            name = elem.find("span", {"class":None}).next_element
            servers[name] = { "lang" : commu }
        time.sleep(3)
    url="https://www.dofus.com/fr/mmorpg/communaute/serveurs?server_access%5B%5D=1&server_access%5B%5D=0#jt_list"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find("table").find("tbody").find_all("tr")
    for elem in results:
        name = elem.find("span", {"class":None}).next_element
        if name not in servers :
            servers[name] = { "lang" : None }
    for name in servers:
        cursor.execute('INSERT INTO server (name, lang) VALUES (%s, %s)', (name, servers[name]["lang"]))
        db.commit()
    print(servers)
    # add wanted notices
    url="https://www.dofus.com/fr/mmorpg/encyclopedie/monstres?monster_category[]=32&monster_category[]=156&monster_category[]=127&monster_category[]=90"
    print('Scraping notices')
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find("table").find("tbody").find_all("tr")
    for elem in results:
       nameFr = elem.find("a").getText()
       img = elem.find("img")["src"]

       cursor.execute(
            'INSERT INTO monster (nameFr, img, zoneId, monsterType)'
            ' VALUES (%s, %s, %s, %s)',
            (nameFr, img, -1, 2)
       )
       db.commit()

    print('Scraped ! Waiting 3s ...')
    time.sleep(3)


    # add cania bandits
    for name in ["Eratz le revendicateur", "Nomekop le Crapoteur", "Edasse le Trouble Fête"]:
        cursor.execute(
           'INSERT INTO monster (nameFr, img, zoneId, monsterType)'
           ' VALUES (%s, %s, %s, %s)',
           (name, "", -1, 3)
        )
        db.commit()


    # add archimonsters
    url="https://www.dofus.com/fr/mmorpg/encyclopedie/monstres?monster_type[0]=archimonster&size=96&page="
    n_pages=3
    for i in range(1,n_pages+1):
        print('Scraping page',i,'/',n_pages)
        page = requests.get(url + str(i))
        soup = BeautifulSoup(page.content, 'html.parser')
        results = soup.find("table").find("tbody").find_all("tr")
        for elem in results:
            nameFr = elem.find("a").getText()
            img = elem.find("img")["src"]

            cursor.execute(
                'INSERT INTO monster (nameFr, img, zoneId, monsterType)'
                ' VALUES (%s, %s, %s, %s)',
                (nameFr, img, -1, 1)
            )
            db.commit()
            
        print('Scraped ! Waiting 3s ...')
        time.sleep(3)


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
