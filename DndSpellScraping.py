# Scraping dnd spells from http://dnd5e.wikidot.com/spells

from bs4 import BeautifulSoup
from urllib.request import urlopen
from pprint import pprint
from time import sleep
import csv

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

    spellleveltables = pagesoup.find_all('table')

    maxspellinfo = []
    maxspelllen = 0

    #parse_spellpage("http://dnd5e.wikidot.com/spell:weird",
    #                maxspellinfo)
    #pprint(maxspellinfo)

    for spelllevel, spell_level_table in enumerate(spellleveltables):
        print(f"Going through spell level {spelllevel}")
        spells = spell_level_table.find_all('tr')
        for spell in spells[1:]:
            spellinfo = []
            spellinfo_bs = spell.find_all("td")

            # TODO: parse better than string
            spellinfo.append(spelllevel)                # Level
            spellinfo.append(spellinfo_bs[0].text)    # Name
            spellinfo.append(spellinfo_bs[1].text)    # School
            spellinfo.append(spellinfo_bs[2].text)    # Casting time
            spellinfo.append(spellinfo_bs[3].text)    # Range
            spellinfo.append(spellinfo_bs[4].text)    # Duration
            spellinfo.append(spellinfo_bs[5].text)    # Components

            # Navigate into spell page
            spellurl = wikidot_url + spellinfo_bs[0].a['href']
            desclen = parse_spellpage(spellurl, spellinfo)
            if (desclen > maxspelllen):
                maxspelllen = desclen
                maxspellinfo = spellinfo

            #spelllists_start = desc_end

            # Check for upcasting
            #spellpage_emp = spellpage_bs.find_all("strong")
            #if len(spellpage_emp) == 6:
            #    spelllists_start += 1

            pprint(spellinfo)
            #sleep(10)
        spelllevel += 1;

    pprint(maxspellinfo)
