#!/usr/bin/env python
# -*- coding:UTF-8 -*-

from bs4 import BeautifulSoup
import requests
from time import sleep
import datetime
import pandas as pd

# column_headers array contains the names for the columns.
column_headers = ["ID", "Title", "Release", "Genres", "Theme",
                  "INTELCPU1", "AMDCPU1", "NVIDIAGPU1", "AMDGPU1", "VRAM1", "RAM1", "OS1", "DX1", "HDD1",
                  "INTELCPU2", "AMDCPU2", "NVIDIAGPU2", "AMDGPU2", "VRAM2", "RAM2", "OS2", "DX2", "HDD2",
                  "INTELCPU3", "AMDCPU3", "NVIDIAGPU3", "AMDGPU3", "VRAM3", "RAM3", "OS3", "DX3", "HDD3"]

spec_header = ["INTELCPU", "AMDCPU", "NVIDIAGPU", "AMDGPU", "RAM", "OS", "DX", "HDD"]


class Scraper:

    # make the parsed soup in to a variable called "soup"
    def __init__(self, url):

        self.url = url
        game_id = url.rsplit("=", 1)
        self.id = int(game_id[1])
        self.datastorage = {}

        # initialize the datastorage[] dict
        for header in column_headers:
            self.datastorage[header] = '-'

        # store the id
        self.datastorage["ID"] = str(self.id)
        # include possible spoofed header, and get the page
        header = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=header)

        # make some soup
        self.soup = BeautifulSoup(r.text.encode('utf-8', 'ignore'), 'html.parser')

    # we go thru the datastorage[] dict and write the info to a string, separated with ';'
    def info_to_string(self):

        info_string = ""

        # write the columns to a single string, place a ';' in between
        for header in column_headers:
            info_string += ';'
            info_string += self.datastorage[header].strip()

        # get rid of the first ;
        info_string = info_string.replace(";", "", 1)

        return info_string

    def format_date(self, unformatted):

        # Mar-26-2010 eg. -> 26-03-2010
        months_dict = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9,
                       'Oct': 10, 'Nov': 11, 'Dec': 12}

        if unformatted.count('-') != 2:
            return unformatted

        rel_date = unformatted.split('-')

        for month in months_dict:
            if month == rel_date[0]:
                formatted = ""
                formatted += rel_date[1]
                formatted += '-'
                formatted += str(months_dict[month])
                formatted += '-'
                formatted += rel_date[2]

                return formatted

        return unformatted

    def get_rel_date(self):
        info_wrapper = self.soup.find("div", "g_wrapper")
        rel_date_str = info_wrapper.find("div", "game-release-date").select('p')[1]
        rel_date = datetime.datetime.strptime(rel_date_str.text, '%d %b %Y ')
        self.datastorage['Release'] = rel_date

    def get_genre_theme(self):
        # find the proper container, and see if theres a genre and theme to be collected
        info_wrapper = self.soup.find("div", "g_wrapper")
        genre_divs = info_wrapper.findAll("div", "gameGenreRow")

        if len(genre_divs) > 1:
            print(f'more genre divs, url: {self.url}')
        # todo: dodělat to parsování
        try:
            self.datastorage["Genres"] = genre_divs[0].text.split('\n')[2].split(', ')
        except AttributeError:
            # attribute errors are ok, there is the default value "-" already there
            pass

        try:
            self.datastorage["Theme"] = genre_divs[1].text.replace("Theme", "").strip()
        except (AttributeError, IndexError):
            pass

    def read_column(self, req_column):

        # we read the column title first to know what requirements we are dealing with (minimum, recommended, gd adj.)
        req_type = req_column.find("div", "systemRequirementsTitle")
        req_number = 0
        if "Minimum" in req_type.text:
            req_number = 1
        elif "Recommended" in req_type.text or "Predicted" in req_type.text:
            req_number = 2
        elif "GD Adjusted" in req_type.text:
            req_number = 3
        else:
            print(self.url)

        # we get the actual rows, and start collecting the data, and storing them in .datastorage

        req_column_inner = req_column.find("div", 'system-requirements-box')
        rows = req_column_inner.findAll("div", recursive=False)
        cpu_gpu_boxes = req_column_inner.findAll('div', 'systemRequirementsHwBox')
        # read the cpus
        cpu_box = cpu_gpu_boxes[0]
        intel_box = cpu_box.find("div", "systemRequirementsLinkSubTop")
        try:
            self.datastorage["INTELCPU" + str(req_number)] = intel_box.find('a').text.strip()
        except AttributeError:
            pass
        amb_box = cpu_box.find("div", "systemRequirementsLinkSubBtm")
        try:
            self.datastorage["AMDCPU" + str(req_number)] = amb_box.find('a').text.strip()
        except AttributeError:
            pass

        # gpus
        gpu_box = cpu_gpu_boxes[1]
        intel_box = gpu_box.find("div", "systemRequirementsLinkSubTop")
        try:
            self.datastorage["NVIDIAGPU" + str(req_number)] = intel_box.find('a').text.strip()
        except AttributeError:
            pass
        amb_box = gpu_box.find("div", "systemRequirementsLinkSubBtm")
        try:
            self.datastorage["AMDGPU" + str(req_number)] = amb_box.find('a').text.strip()
        except AttributeError:
            pass

        # vram
        spec = req_column.find("div", 'systemRequirementsHwBoxVRAM' + ('Min' if req_number == 1 else '')).find('div')
        try:
            self.datastorage["VRAM" + str(req_number)] = spec.text.strip()
        except AttributeError:
            pass

        # ram
        spec = req_column.find("div", 'systemRequirementsHwBoxRAM' + ('Min' if req_number == 1 else '')).find('div')
        try:
            self.datastorage["RAM" + str(req_number)] = spec.text.strip()
        except AttributeError:
            pass

        # os
        spec = req_column.find("div", 'systemRequirementsHwBoxSystem' + ('Min' if req_number == 1 else '')).find('div')
        try:
            self.datastorage["OS" + str(req_number)] = spec.text.strip()
        except AttributeError:
            pass

        # direct x
        spec = req_column.find("div", 'systemRequirementsHwBoxDirectX' + ('Min' if req_number == 1 else '')).find('div')
        try:
            self.datastorage["DX" + str(req_number)] = spec.text.strip()
        except AttributeError:
            pass

        # hdd
        spec = rows[6]
        try:
            self.datastorage["HDD" + str(req_number)] = spec.text.strip()
        except AttributeError:
            pass

    def parse_requirements(self):
        pass

    def get_requirements(self):
        spec_box = self.soup.find("div", id="systemRequirementsOuterBox")

        # no specs found, lets go away
        if spec_box is None:
            return

        # # check if the rows have the same title allways
        # row_titles = spec_box.find("div", id="systemRequirementsSubheadWrap")

        # since there was a OuterBox, we have atleast some sp
        req_columns = spec_box.findAll("div", "systemRequirementsWrapBox gameSystemRequirementsWrapBox")

        for req_column in req_columns:
            self.read_column(req_column)

    # do the actual scraping
    def get_pageinfo(self):

        # do the actual scraping here
        soup = self.soup

        # Title
        try:
            art_title = soup.find("div", id="art_g_title").text
            self.datastorage["Title"] = soup.find("div", "game-title-container").text.strip()
            if "[ Android ]" in art_title or "[]" in art_title or "[ IOS ]" in art_title:
                return None
        except AttributeError:
            # print self.url
            return None

        # release dates
        self.get_rel_date()

        # genre and theme
        self.get_genre_theme()

        # now the actual specs
        self.get_requirements()

        # after all the info is in the datastorage[] dictionary, we write it to a single string and return
        return self.datastorage

    # member variables
    soup = None
    datastorage = {}
    url = ""
    id = 0


if __name__ == "__main__":

    # insert the base of the url's we're going to scare
    baseurl = "http://www.game-debate.com/games/index.php?g_id="

    with open('last_index.txt', 'r') as f:
        # lowest id which actually contains a game is 12
        starting_id = int(f.read()) + 1

    # the file we are gonna write the gotten info, the file has the starting_id in it, in case starting
    # from somewhere else than the begining.
    output_file = f"game-debate_start_{starting_id}.csv"
    df = pd.DataFrame(columns=column_headers)

    print(f"starting with ID: {starting_id} in {datetime.datetime.now()}")

    # loop the games from starting_id to end. Heuristic number that should tell number of games
    for i in range(starting_id, 7350):
        print(f"processing ID: {i} in {datetime.datetime.now()}")
        # get the page, BS it, and get the pageinfo
        page_to_get = Scraper(f'{baseurl}{i}')
        page_info = page_to_get.get_pageinfo()

        # if we didnt get anything back (no info etc), we skip the writing
        if page_info is None:
            continue

        df = df.append(page_info, ignore_index=True)

        with open('last_index.txt', 'w') as f:
            f.write(f'{i}')

        # be nice, the longer the better
        if i % 100 == 0:
            df.to_csv(f"game-debate_start_{starting_id}_{i}.csv", index=False)
            print(f'persisting file after ID {i}')
        sleep(1)

    df.to_csv(output_file, index=False)
