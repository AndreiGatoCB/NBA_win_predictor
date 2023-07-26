import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
import time
import re
import numpy as np
import os
import lxml.html

                                            ####################
                                            ## PARSE NBA DATA ##
                                            ####################
def get_html(url, label, clase, id='all_schedule'):
    page = requests.get(url)
    soup = bs(page.content, 'html.parser')
    title = soup.find('title').text
    print(title)
    if label == '':
        html = soup.find_all(id=id)

    else:
        html = soup.find_all(label, class_=clase)

    return str(html), title


def scrape_season(season):
    url = f'https://www.basketball-reference.com/leagues/NBA_{season}_games.html'
    months = get_html(url, 'div', 'filter')
    soup = bs(months[0], 'lxml')
    months_links = soup.find_all('a', href=True)
    href = [i['href'] for i in months_links ]

    standing_pages = [f'https://www.basketball-reference.com{l}' for l in href]

    return standing_pages


def box_scores(stand_page: str):
    response = requests.get(stand_page)
    html = response.text
    soup = bs(html)
    links = soup.find_all('a')
    hrefs = [l.get('href') for l in links]
    box_scores = [l for l in hrefs]
    box_scores = [f'https://www.basketball-reference.com{l}' for l in box_scores]
    box_scores = list(filter(lambda url: 'boxscores/' in url and url.endswith('html'), box_scores))
    return box_scores


def parse_html(box_score):
    response = requests.get(box_score)
    html = response.content
    html_ = re.sub(r'<!--', '', html.decode())
    soup = bs(html_, 'html.parser')
    return soup


def read_line_score(soup):
    table = pd.read_html(str(soup.select_one('#div_line_score')))
    table_ = table[-1].rename(columns={'Unnamed: 0_level_1': 'team', 'T': 'total'})
    table_.columns = table_.columns.droplevel(0)
    line_score = table_[['team', 'total']]
    return line_score


def read_stats(soup, team, stat) -> pd.DataFrame:
    stats = pd.read_html(str(soup), attrs={'id': f'box-{team}-game-{stat}'}, index_col=0)[0]
    stats.columns = stats.columns.droplevel(0)
    stats = stats.drop(stats[stats['MP'] == 'MP'].index)
    stats.replace(np.nan, 0, inplace=True)
    return stats


def read_season_info(soup):
    nav = soup.select('#bottom_nav_container')[0]
    hrefs = [a['href'] for a in nav.find_all('a') if '.html' in a['href'] and 'teams' in a['href']]
    season = re.search(r'\d+', hrefs[0]).group()
    return season


                                            ##################
                                            ## GET NBA DATA ##
                                            ##################


