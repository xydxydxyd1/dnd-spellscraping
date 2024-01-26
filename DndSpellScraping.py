# Scraping dnd spells from http://dnd5e.wikidot.com/spells

from bs4 import BeautifulSoup
from urllib.request import urlopen
from pprint import pprint
import csv

# Parse the spell row for basic information
def parse_spellrow(tdarr, spellinfo):
    # TODO: parse better than string
    spellinfo.append(spelllevel)                # Level
    spellinfo.append(tdarr[0].text)    # Name
    spellinfo.append(tdarr[1].text)    # School
    spellinfo.append(tdarr[2].text)    # Casting time
    spellinfo.append(tdarr[3].text)    # Range
    spellinfo.append(tdarr[4].text)    # Duration
    spellinfo.append(tdarr[5].text)    # Components

# Parse the spell page for description, upcasting, and spelllists to be
# appended to spellinfo
# Return the length of the description
def parse_spellpage(url, spellinfo):
    spellpage_bs = BeautifulSoup(
            urlopen(url).read().decode("utf-8"),
            "html.parser") \
            .find_all(id="page-content")[0]
    pars = spellpage_bs.find_all("p")

    # Spell description pars[desc_start:desc_end].text
    desc_start = 3
    desc_end = 4
    while True:
        if pars[desc_end].text.startswith("Spell Lists") \
                or pars[desc_end].text.startswith("At Higher Levels"):
            break
        desc_end += 1
    desc = ""
    for par in pars[desc_start:desc_end]:
        desc += par.text
        desc += "\n"
    spellinfo.append(desc)                      # Desc.

    return len(desc)

if __name__ == "__main__":
    # Open main spell page
    wikidot_url = "http://dnd5e.wikidot.com"
    page = urlopen(wikidot_url + "/spells")
    html = page.read().decode("utf-8")
    pagesoup = BeautifulSoup(html, "html.parser")

    # spellleveltable[i] is a table containing spells of level i
    spellleveltables = pagesoup.find_all('table')

    for spelllevel, spell_level_table in enumerate(spellleveltables):
        print(f"Going through spell level {spelllevel}")
        spells = spell_level_table.find_all('tr')
        for spellrow in spells[1:]:
            spellinfo = []
            spellinfo_bs = spellrow.find_all("td")

            parse_spellrow(spellrow, spellinfo)

            # Navigate into spell page and parse it
            spellurl = wikidot_url + spellinfo_bs[0].a['href']
            parse_spellpage(spellurl, spellinfo)

            pprint(spellinfo)
        spelllevel += 1;
