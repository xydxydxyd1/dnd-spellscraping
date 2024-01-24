# Scraping dnd spells from http://dnd5e.wikidot.com/spells

from bs4 import BeautifulSoup
from urllib.request import urlopen
import csv

if __name__ == "__main__":
    # Open main spell page
    wikidot_url = "http://dnd5e.wikidot.com"
    page = urlopen(wikidot_url + "/spells")
    html = page.read().decode("utf-8")
    pagesoup = BeautifulSoup(html, "html.parser")

    spellleveltables = pagesoup.find_all('table')
    with open("spells.csv", "w") as spellcsv:
        for spelllevel, spell_level_table in enumerate(spellleveltables):
            spells = spell_level_table.find_all('tr')
            for spell in spells[1:]:
                spellinfo = []
                spellinfo_bs = spell.find_all("td")

                # TODO: parse better than string
                spellinfo.append(spellinfo_bs[0].string)    # Name
                spellinfo.append(spellinfo_bs[1].string)    # School
                spellinfo.append(spellinfo_bs[2].string)    # Casting time
                spellinfo.append(spellinfo_bs[3].string)    # Range
                spellinfo.append(spellinfo_bs[4].string)    # Duration
                spellinfo.append(spellinfo_bs[5].string)    # Components

                # Navigate into spell page
                spellurl = wikidot_url + spellinfo_bs[0].a['href']
                spellpage_bs = BeautifulSoup(
                        urlopen(spellurl).read().decode("utf-8"),
                        "html.parser") \
                        .find_all(id="page-content")[0]

                # Spell description pars[desc_start:desc_end].string
                pars = spellpage_bs.find_all("p")
                desc_start = 3
                desc_end = 4
                while True:
                    break
                print(pars[desc_start:desc_end])

                # Check for upcasting
                spellpage_emp = spellpage_bs.find_all("strong")
                if len(spellpage_emp) == 6:
                    print("Upcasted!")

                print(spellinfo)
                exit()
            spelllevel += 1;
