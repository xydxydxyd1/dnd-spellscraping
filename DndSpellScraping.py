# Scraping dnd spells from http://dnd5e.wikidot.com/spells

from bs4 import BeautifulSoup
import bs4
from urllib.request import urlopen
from pprint import pprint
import csv
from markdownify import MarkdownConverter

# Create shorthand method for conversion
def md(soup, **options):
    return MarkdownConverter(**options).convert_soup(soup)

# Parse the spell row for basic information
def parse_spellrow(tdarr, spellinfo, spelllevel):
    # TODO: parse better than string
    tags = ""
    spellinfo.append(spelllevel)                # Level
    spellinfo.append(tdarr[0].text)    # Name
    tags = extract_school(tdarr[1], spellinfo, tags)
    tags = extract_casttime(tdarr[2], spellinfo, tags)
    spellinfo.append(tdarr[3].text)    # Range
    spellinfo.append(tdarr[4].text)    # Duration
    spellinfo.append(tdarr[5].text)    # Components

    spellinfo.append(tags)

# Parse the school soup for casting time and ritual
# Append school to spellinfo and return new tags
def extract_school(soup, spellinfo, tags):
    school = soup.text
    if soup.sup:
        school = school[:-2]
        match soup.sup.text:
            case "D":
                tags += "Dunamancy"
            case "DG":
                tags += "Graviturgy"
            case "DC":
                tags += "Chronurgy"
            case "HB":
                tags += "Homebrew"
            case "T":
                tags += "Technomagic"
    spellinfo.append(school)
    return tags

# Parse the casting time soup for casting time and ritual
# Append casting time to spellinfo and return new tags
def extract_casttime(soup, spellinfo, tags):
    casttime = soup.text
    if soup.sup:
        tags += "Ritual, "
        casttime = casttime[:-2]
    spellinfo.append(casttime)
    return tags

# Parse the spell page for description, upcasting, and spelllists to be
# appended to spellinfo
# Return the length of the description
def parse_spellpage(url, spellinfo):
    spellpage_bs = BeautifulSoup(
            urlopen(url).read().decode("utf-8"),
            "html.parser") \
            .find_all(id="page-content")[0]

    cursor = None;

    cursor = extract_description(spellpage_bs, spellinfo)
    cursor = extract_upcast(cursor, spellinfo)
    cursor = extract_spelllist(cursor, spellinfo)

    # Spell description pars[desc_start:desc_end].text
    #desc_end = 4
    #while True:
    #    if pars[desc_end].text.startswith("Spell Lists") \
    #            or pars[desc_end].text.startswith("At Higher Levels"):
    #        break
    #    desc_end += 1
    #desc = ""
    #for par in pars[desc_start:desc_end]:
    #    desc += par.text
    #    desc += "\n"
    #spellinfo.append(desc)                      # Desc.

    #return len(desc)

# Extract description from spell page soup and append it to spellinfo.
# Return the soup tag after description (spell list or upcast)
def extract_description(spellpage_bs, spellinfo):
    # Navigate to right before the first description tag
    desc_start = spellpage_bs.find_all("p")[2]
    desc = ""
    desc_end = None

    for sibling in desc_start.next_siblings:
        if sibling.text.startswith("Spell Lists") \
                or sibling.text.startswith("At Higher Levels"):
            desc_end = sibling
            break
        if not isinstance(sibling, bs4.element.Tag):
            continue
        desc += md(sibling) + "\n\n"

    spellinfo.append(desc)
    return desc_end

# Extract upcasting from spell page and append it to spellinfo.
# Return the p tag after upcasting or the same tag if no upcasting
def extract_upcast(cursor, spellinfo):
    if cursor.text.startswith("At Higher Levels"):
        spellinfo.append(cursor.text)
        return cursor.find_next("p")

    spellinfo.append("")
    return cursor

# Extract spell list from spell page and append it to spellinfo.
# Return the sibling after spell lists
def extract_spelllist(cursor, spellinfo):
    spelllists = ""
    if cursor.text.startswith("Spell Lists"):
        for spelllist in cursor.find_all("a"):
            spelllists += spelllist.text + ", "
    spellinfo.append(spelllists)
    return cursor.next_sibling

if __name__ == "__main__":
    # Open main spell page
    wikidot_url = "http://dnd5e.wikidot.com"
    page = urlopen(wikidot_url + "/spells")
    html = page.read().decode("utf-8")
    pagesoup = BeautifulSoup(html, "html.parser")

    # spellleveltable[i] is a table containing spells of level i
    spellleveltables = pagesoup.find_all('table')

    # Test
    #spellinfo_bs = spellleveltables[8].find_all('tr')[7].find_all("td")
    #spellinfo = []
    #print(spellinfo_bs)
    #parse_spellrow(spellinfo_bs, spellinfo, 2)
    #exit()

    with open('spells.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        spellinfo = [
                "Level",
                "Name",
                "School",
                "Cast Time",
                "Range",
                "Duration",
                "Components",
                "Tags",
                "Description",
                "Upcasting",
                "Spell Lists",
                ]
        csvwriter.writerow(spellinfo)
        for spelllevel, spell_level_table in enumerate(spellleveltables):

            print(f"Going through spell level {spelllevel}")
            spells = spell_level_table.find_all('tr')
            for spellrow in spells[1:]:
                spellinfo = []
                spellinfo_bs = spellrow.find_all("td")

                parse_spellrow(spellinfo_bs, spellinfo, spelllevel)

                # Navigate into spell page and parse it
                spellurl = wikidot_url + spellinfo_bs[0].a['href']
                parse_spellpage(spellurl, spellinfo)

                print(f"Level: {spelllevel}\tName: {spellinfo[1]}")
                csvwriter.writerow(spellinfo)
            spelllevel += 1
