# Scraping dnd spells from http://dnd5e.wikidot.com/spells

from bs4 import BeautifulSoup
import bs4
from urllib.request import urlopen
from pprint import pprint
import csv
from markdownify import MarkdownConverter
import re

class TableConverter(MarkdownConverter):
    """
    Custom markdown converter that correctly converts rows that span
    multiple columns
    """
    def convert_tr(self, el, text, convert_as_inline):
        cells = el.find_all(['td', 'th'])
        is_headrow = all([cell.name == 'th' for cell in cells])
        overline = ''
        underline = ''
        if is_headrow and not el.previous_sibling:
            # first row and is headline: print headline underline
            colcnt = 0
            for cell in cells:
                if "colspan" in cell.attrs:
                    colcnt += int(cell["colspan"])
                else:
                    colcnt += 1

            underline += '| ' + ' | '.join(['---'] * colcnt) + ' |' + '\n'
        elif (not el.previous_sibling
              and (el.parent.name == 'table'
                   or (el.parent.name == 'tbody'
                       and not el.parent.previous_sibling))):
            # first row, not headline, and:
            # - the parent is table or
            # - the parent is tbody at the beginning of a table.
            # print empty headline above this row
            overline += '| ' + ' | '.join([''] * len(cells)) + ' |' + '\n'
            overline += '| ' + ' | '.join(['---'] * len(cells)) + ' |' + '\n'
        return overline + '|' + text + '\n' + underline

    def convert_td(self, el, text, convert_as_inline):
        colspan = 1
        if 'colspan' in el.attrs:
            colspan = int(el['colspan'])
        return ' ' + text + ' |' * colspan

    def convert_th(self, el, text, convert_as_inline):
        colspan = 1
        if 'colspan' in el.attrs:
            colspan = int(el['colspan'])
        return ' ' + text + ' |' * colspan

def md(soup, **options):
    """Shorthand method for converting bs4 to markdown"""
    return TableConverter(**options).convert_soup(soup)

def parse_spellrow(tdarr, spellinfo, spelllevel):
    """Parse the spell row for basic information"""
    # TODO: parse better than string
    tags = []
    spellinfo.append(spelllevel)                # Level
    spellinfo.append(tdarr[0].text)    # Name
    extract_school(tdarr[1], spellinfo, tags)
    extract_casttime(tdarr[2], spellinfo, tags)
    extract_range_aoe(tdarr[3], spellinfo)
    extract_duration(tdarr[4], spellinfo, tags)
    spellinfo.append(tdarr[5].text)    # Components

    spellinfo.append(", ".join(tags))

def extract_range_aoe(soup, spellinfo):
    """ Extract area of effect from range soup and append them to
    spellinfo
    """
    spellrange = soup.text
    aoe = ""

    range_pattern = re.compile(r"^(.*) \((.*)\).*$")
    match = range_pattern.findall(soup.text)
    if len(match) > 0:
        spellrange, aoe = match[0]

    spellinfo.append(spellrange)
    spellinfo.append(aoe)

# Parse the duration soup for duration and concentration
# Append duration to spellinfo and return new tags
def extract_duration(soup, spellinfo, tags):
    duration = soup.text

    if duration.startswith("Concentration"):
        tags.append("Concentration")
        con_pattern = re.compile("Concentration,? [uU]p to (.*)")
        try:
            duration = con_pattern.findall(duration)[0]
        except Exception as e:
            print("Duration is weird: ", duration)
            duration = "None"

    spellinfo.append(duration)

# Parse the school soup for casting time and ritual
# Append school to spellinfo and return new tags
def extract_school(soup, spellinfo, tags):
    school = soup.text
    if soup.sup:
        school = school[:-2]
        match soup.sup.text:
            case "D":
                tags.append("Dunamancy")
            case "DG":
                tags.append("Graviturgy")
            case "DC":
                tags.append("Chronurgy")
            case "HB":
                tags.append("Homebrew")
            case "T":
                tags.append("Technomagic")
    spellinfo.append(school)

# Parse the casting time soup for casting time and ritual
# Append casting time to spellinfo and return new tags
def extract_casttime(soup, spellinfo, tags):
    casttime = soup.text
    if soup.sup:
        tags.append("Ritual")
        casttime = casttime[:-2]
    spellinfo.append(casttime.lower())

def parse_spellpage(url, spellinfo):
    """Parse the spell page for description, upcasting, and spelllists
    to be appended to spellinfo

    Return the length of the description
    """
    spellpage_bs = BeautifulSoup(
            urlopen(url).read().decode("utf-8"),
            "html.parser") \
            .find_all(id="page-content")[0]

    extract_component(spellpage_bs, spellinfo)

    # cursor helps parsing adjacent items
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

def extract_component(spellpage_bs, spellinfo):
    """ Extract the material component from spell page soup and append
    it to spellinfo
    """
    spell_specs = spellpage_bs.find_all("p")[2].text
    comp_pattern = re.compile(r"^Components:.*\((.*)\).*$", re.MULTILINE)
    component = comp_pattern.findall(spell_specs)
    spellinfo.append(','.join(component))

# Extract description from spell page soup and append it to spellinfo,
# and uses the extracted description to extract dice and ability
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
        desc += md(sibling, strip=['a']) + "\n\n"

    spellinfo.append(desc)

    extract_dice_and_ability(desc, spellinfo)

    return desc_end

# Extract dice roll and relevant abilities from description, appending
# them to spellinfo.
# Example: spellinfo.append("d8, DEX")
def extract_dice_and_ability(desc, spellinfo):
    abilities_pattern = re.compile(r"(?:Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)")
    dice_pattern = re.compile(r'\b(\d*d\d+)\b')
    abilities = ",".join(list(set(abilities_pattern.findall(desc))))
    dicerolls = ",".join(list(set(dice_pattern.findall(desc))))

    spellinfo.append(dicerolls)
    spellinfo.append(abilities)
    return


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
    #spellinfo = []

    #spellinfo_bs = spellleveltables[3].find_all('tr')[5].find_all("td")
    #print(spellinfo_bs)
    #parse_spellrow(spellinfo_bs, spellinfo, 2)

    #parse_spellpage("http://dnd5e.wikidot.com/spell:delayed-blast-fireball",
    #                spellinfo)

    #pprint(spellinfo)
    #exit()

    with open('spells.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        spellinfo = [
                "Level",
                "Name",
                "School",
                "Cast Time",
                "Range",
                "AoE",
                "Duration",
                "Components",
                "Tags",
                "Materials",
                "Description",
                "Diceroll",
                "Abilities",
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
