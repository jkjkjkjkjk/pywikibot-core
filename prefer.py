#!/usr/bin/python3
import pywikibot
import requests
import json
import re

# Are we testing or are we for real?
TEST = False
COMMIT = True
"""
This bot does the following:
for the specified set of items, for properties that
have start/end time qualifiers, and only one current (start time, no end time)
claim that claim is made preferred
"""
if TEST:
    site = pywikibot.Site("test", "wikidata")
    START_TIME = 'P355'
    END_TIME = 'P356'
    DEATH_DATE = 'P570'
    props = ['P141']
else:
    START_TIME = 'P580'
    END_TIME = 'P582'
    DEATH_DATE = 'P570'
    site = pywikibot.Site("wikidata", "wikidata")

LOGPAGE = "User:PreferentialBot/Log/"
qregex = re.compile('{{Q|(Q\d+)}}')
repo = site.data_repository()

def get_items(prop, bad_ids=[]):
    SPARQL = "http://query.wikidata.org/bigdata/namespace/wdq/sparql"
    QUERY = """
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX q: <http://www.wikidata.org/prop/qualifier/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
prefix wd: <http://www.wikidata.org/entity/>
SELECT DISTINCT ?s WHERE {
  BIND (p:%s as ?prop)
  ?s ?prop ?st .
# One claim with start time
  ?st q:P580 ?t .
# and no end time
  OPTIONAL { ?st q:P582 ?t2 }
  FILTER(!bound(?t2))
  ?st wikibase:rank wikibase:NormalRank.
# Another claim
  ?s ?prop ?st2 .
  FILTER(?st2 != ?st)
# with an end time
  ?st2 q:P582 ?t3 .
# and it's not a dead person
  OPTIONAL { ?s wdt:P570 ?d }
  FILTER(!bound(?d))
  ?st2 wikibase:rank wikibase:NormalRank.
  %s
} LIMIT 10
"""
# Query asks for items with normal-ranked statement with start date
# and no end date, more than one statement on the same property
# and not date of death for this item
    if len(bad_ids) > 0:
        id_filter = "MINUS { VALUES ?s { %s } }" % ' '.join(["wd:"+q for q in bad_ids if q ])
    else:
        id_filter = ''

    dquery = QUERY % (prop, id_filter) 
    print(dquery)

    resp = requests.get(SPARQL, 
        params={ 'query': dquery },
        headers={ 'cache-control':'no-cache',
                                     'Accept': 'application/sparql-results+json'
                            })
    if resp.status_code != 200 or not resp.text:
        print("Query on %s failed" % prop)
        print(resp)
        return []
    data = resp.json()
    items = []
    if 'results' in data:
        for r in data['results']['bindings']:
            items.append(r['s']['value'][31:])
    return items

def load_page(page):
    return set(qregex.findall(page.text))

def log_item(page, item, reason):
    print("%s on %s" %(reason, item))
    if page.text.find(item+"}}") != -1:
        # already there
        return
    page.text = page.text.strip() + "\n* {{Q|%s}} %s" % (item, reason)
    page.modifiedByBot = True
    pass

"""
Test entities for P6:
wd:Q5870
wd:Q148
wd:Q5906
wd:Q6441
wd:Q10483
wd:Q1718
wd:Q826
wd:Q891
wd:Q2948
wd:Q3936
"""
"""
Too many bad entries:
P54: member of the sports team
P102: member of political party
P131: located in the administrative territorial entity
P195: collection
P551
P579: IMA status and/or rank
"""
"""
P6: head of government
P17: country
P26: spouse
P35: head of state
P36: capital
P94: coat of arms image
P115: home venue
P118: league
P123: publisher
P138: named after
P154: logo image
P159: headquarters location
P169: chief executive officer
P176: manufacturer
P286: head coach
P289: vessel class
P449: original network
P484: IMA Number, broad sense
P488: chairperson
P551: residence
P579: IMA status and/or rank
P598: commander of
P605: NUTS code
P625: coordinate location
P708: diocese
P749: parent company
P879: pennant number
P964: Austrian municipality key
P1037: manager/director
P1075: rector
P1308: officeholder
P1435: heritage status
P1448: official name
P1454: legal form
P1476: title
P1705: native label
P1813: short name
P1998: UCI code
"""
if not TEST:
    props = [
             'P26', 'P6', 'P17', 'P35', 'P36', 'P94', 'P115', 'P118', 'P123', 'P138', 'P154', 'P159', 'P169', 'P176',
             'P286', 'P289', 'P449', 'P484', 'P488', 'P551', 'P598', 'P605', 'P625',
             'P708', 'P749', 'P879', 'P964', 'P1037','P1075', 'P1308', 'P1435', 'P1448', 'P1454',
             'P1476', 'P1705', 'P1813', 'P1998'
    ]

for prop in props:
    logpage = pywikibot.Page(site, LOGPAGE+prop)
    logpage.modifiedByBot = False
    baditems = load_page(logpage)
    if len(baditems) > 30:
        print("Too many bad items for %s, skipping" % prop)
        continue
    if TEST:
        items = ["Q826"]
    else:
        items = get_items(prop, baditems)
    print("Property %s items %s" % (prop, items))
    for itemID in items:
        if itemID in baditems:
            print("Known bad item %s, skip" % itemID)
            continue

        item = pywikibot.ItemPage(repo, itemID)
        item.get()

        if prop not in item.claims:
            print("Hmm, no %s for %s" % (prop, itemID))
            continue

        if len(item.claims[prop]) < 2:
            # if there are less than two, no reason to bother
            print("Sole %s for %s, don't bother" % (prop, itemID))
            continue
        foundPreferred = False
        for statement in item.claims[prop]:
            if statement.rank == 'preferred':
                # if there's already preferred statement here, we should not intervene
                foundPreferred = True
                break
        if foundPreferred:
            print("Already have preference for %s on %s, skip" % (prop, itemID))
            continue

        if DEATH_DATE in item.claims:
            log_item(logpage, itemID, "Death date specified")
            continue

        bestRanked = []
        for statement in item.claims[prop]:
            if START_TIME not in statement.qualifiers:
                if END_TIME in statement.qualifiers and statement.qualifiers[END_TIME][0].getSnakType() != 'novalue':
                    # has end time, then allow not to have start time
                    continue
                # no start or more than one start - this one is weird
                log_item(logpage, itemID, "Missing start qualifier")
                bestRanked = []
                break
            if len(statement.qualifiers[START_TIME])>1:
                if END_TIME in statement.qualifiers and len(statement.qualifiers[START_TIME]) == len(statement.qualifiers[END_TIME]):
                    # multi matching start-ends are ok
                    continue
                log_item(logpage, itemID, "Multiple start qualifiers")
                bestRanked = []
                break
            if END_TIME in statement.qualifiers:
                if len(statement.qualifiers[END_TIME])>1:
                    log_item(logpage, itemID, "Multiple end qualifiers")
                    # more than one end - weird, skip it
                    bestRanked = []
                    break
                q = statement.qualifiers[END_TIME][0]
                if q.getSnakType() != 'novalue':
                    # skip those that have end values - these are not preferred ones
                    continue
            # has start but no end - that's what we're looking for
            if statement.rank == 'normal':
                bestRanked.append(statement)

        if(len(bestRanked) > 1):
            print("Multiple bests on %s:%s, skip for now" % (itemID, prop))
            log_item(logpage, itemID, "Multiple best statements")
            continue
        for statement in bestRanked:
            print("Marking %s on %s:%s as preferred " % (statement.snak, itemID, prop))
            if COMMIT:
                result = statement.changeRank('preferred')
    if logpage.modifiedByBot:
        logpage.save("log for "+prop)
