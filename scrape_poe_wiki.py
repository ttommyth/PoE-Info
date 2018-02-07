#! python3
"""
This code (was before wiki rework) based largely on:
https://github.com/aRTy42/scrape_poe_info/blob/master/scrape_poe_uniques.py
it still relies on and fetches the file https://raw.githubusercontent.com/aRTy42/scrape_poe_info/master/UniqueStyleVariants.json
"""
from difflib import SequenceMatcher
import requests, re, datetime, time, json, os
import urllib.parse as urlparse
import html
import time

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
##SCRIPTDIR = os.path.dirname(os.path.abspath(__file__))

regex_wikilinks = re.compile(r'\[\[([^\]\|]*)\]\]|\[\[[^\]\|]*\|([^\]\|]*)\]\]')
"""
matches formats "[[mod]]" or "[[wikipage|mod]] and stores "mod" as capture group 1 or 2, respectively.
Since only one capture group is filled each time, using both together in a replacement like r'\1\2' turns
both match variants into "mod".
"""

regex_wiki_page_disamb = re.compile(r'([^\(]+) \([^\)]+\)')
"""
matches items named "item name (disambiguation)" and stores "item name" as capture group 1.
this format is used in the wiki to distinguish style variants of items, giving each variant its own page.
since the style variants ingame all have the same name, we want to filter these out and
put in a manually prepared version that covers all styles in one overview. 
"""

def remove_wiki_formats(text):
        if text is None:
                return None
        text = regex_wikilinks.sub(r'\1\2', text)       # remove wiki links with regular expression. See the start of the script.
        text = text.replace('<em class="tc -corrupted">Corrupted</em>', 'Corrupted')    # remove corrupted markup
        text = text.replace('&#60;', '<').replace('&#62;', '>')
        return text

def remove_hidden_mods(mod_list):
        new_mod_list = []
        for mod in mod_list:
                if '(Hidden)' not in mod:                       # No '(Hidden)' annotation found
                        new_mod_list.append(mod)                # Thus the mod is passed on
        
        return new_mod_list                     

def format_affixes(item_list):
        new_data = []
        
        # manually prepared formatting for style variant items
        
        try:
                r=requests.get('https://raw.githubusercontent.com/aRTy42/scrape_poe_info/master/UniqueStyleVariants.json')
                r.encoding='utf8'
                prepared_style_variants = r.json()
##        with open('UniqueStyleVariants.json', 'r') as f:
##                prepared_style_variants = json.load(f)
        except:
                prepared_style_variants={}
        
        style_variant_included = []
        for item in item_list:
                if regex_wiki_page_disamb.search(item['name']) is not None:
                        item_name = regex_wiki_page_disamb.search(item['name']).group(1)
                        if item_name in prepared_style_variants:
                                if item_name not in style_variant_included:
                                        mod_line = prepared_style_variants[item_name]
                                        expl_mods = mod_line.split('|')[1:]
                                        for i in range(len(expl_mods)):
                                                expl_mods[i] = re.sub('^@.*','',expl_mods[i]) # remove implicits
                                                expl_mods[i] = re.sub('^:','',expl_mods[i])
                                                expl_mods[i] = re.sub('(^\d+-\d+)(:)','(\\1) ',expl_mods[i])
                                                expl_mods[i] = re.sub('(^\d+-\d+),(\d+-\d+)(:)','(\\1)-(\\2) ',expl_mods[i])
                                        item['expl'] = '<br>'.join([mod for mod in expl_mods if not re.match('^\s*$',mod)])
                                        style_variant_included.append(item_name)
##                                        break           # skip the rest of the loop because mod line was added properly
                                else:
                                        continue           # skip the rest of the loop because style variant was already added

                        else:
                                print('Style variant expected but not found for: ' + item['name'] +'\nItem gets parsed as usual and added to the file, double check there.')
                
                mod_line = item['name']
                
                if item['impl']:
                        impl_mod_list = re.split('<br\s*/?\s*>',item['impl'])
                        impl_mod_list = remove_hidden_mods(impl_mod_list)
                        
                        if impl_mod_list:               # mod list is not empty
                                item['impl'] = ' | '.join(impl_mod_list) # in case there are multiple. 
                        else:
                                item['impl'] = None
                
                if item['expl']:
                        expl_mod_list = re.split('<br\s*/?\s*>',item['expl'])
                        expl_mod_list = remove_hidden_mods(expl_mod_list)
                        
                        if expl_mod_list:               # mod list is not empty
                                item['expl'] = '\n'.join(expl_mod_list)
                        else:
                                item['expl'] = None
                new_data.append(item)
                
        print('\nManually prepared style variants included for these items:\n' + '\n'.join(style_variant_included) + '\n(Make sure they are still correct)\n')
        
        return new_data

# cargo wiki field: local sqlitedb field
SKILL_GEM_PROPERTY_MAPPING={
                #skill_gems fields:
                'skill_gems._pageName':'name',
                'skill_gems.gem_description':'gem_desc',
                'skill_gems.support_gem_letter':'support_letter',
                'skill_gems.gem_tags':'tags',
                'skill_gems.primary_attribute':'primary_att',
                'skill_gems.dexterity_percent':'dex_percent',
                'skill_gems.intelligence_percent':'int_percent',
                'skill_gems.strength_percent':'str_percent',
                #skill fields:
                'skill.skill_icon':'image_url',
                'skill.has_reservation_mana_cost':'is_res',
                'skill.quality_stat_text':'qual_bonus',
                'skill.item_class_restriction':'item_restriction',
                'skill.max_level':'max_level',
                'skill.projectile_speed':'proj_speed',
                'skill.cast_time':'cast_time',
                'skill.radius':'radius',
                'skill.radius_secondary':'radius_2',
                'skill.radius_tertiary':'radius_3',
                'skill.radius_description':'radius_desc',
                'skill.radius_secondary_description':'radius_2_desc',
                'skill.radius_tertiary_description':'radius_3_desc',
                #skill_levels fields
                'skill_levels.stat_text':'stat_text',
                'skill_levels.cooldown':'cooldown',
                'skill_levels.critical_strike_chance':'crit_chance',
                'skill_levels.damage_effectiveness':'damage_effectiveness',
                'skill_levels.damage_multiplier':'damage_multiplier',
                'skill_levels.dexterity_requirement':'dex_requirement',
                'skill_levels.experience':'xp',
                'skill_levels.intelligence_requirement':'int_requirement',
                'skill_levels.level_requirement':'level_requirement',
                'skill_levels.mana_cost':'mana_cost',
                'skill_levels.mana_multiplier':'mana_multiplier',
                'skill_levels.stored_uses':'stored_uses',
                'skill_levels.strength_requirement':'str_requirement',
                'skill_levels.vaal_souls_requirement':'vaal_souls_requirement',
                'skill_levels.vaal_stored_uses':'vaal_stored_uses',
        }

def scrape_skill_gems(limit=500):                
        fields_to_fetch = list(SKILL_GEM_PROPERTY_MAPPING.values())
        query = 'https://pathofexile.gamepedia.com/api.php?action=cargoquery&format=json&tables=skill_gems,skill,skill_levels&join_on=skill_gems._pageName=skill._pageName,skill_gems._pageName=skill_levels._pageName&fields='+','.join(['='.join((k,v)) for k,v in SKILL_GEM_PROPERTY_MAPPING.items()])+'&where=skill_levels.level=skill.max_level&group_by=skill_gems._pageName&limit='+str(limit)
        api_results = []
        for i in range(3):
                rj=None
                try:
                        r = requests.get(query)
                        r.encoding = 'utf-8'
                        rj = r.json()
                        api_results = [a['title'] for a in rj['cargoquery']]
                        break
                except:
                        print(rj)
                        time.sleep(4)
        return api_results
'''https://pathofexile.gamepedia.com/api.php?action=cargoquery&tables=skill_gems&fields=_pageName=name,gem_description=gem_desc,EXISTS(support_gem_letter)&limit=10'''
'https://pathofexile.gamepedia.com/api.php?action=cargoquery&tables=items&where=rarity=unique&limit=10'

UNIQUE_ITEM_PROPERTY_MAPPING={
        'items._pageName':'name',
        'items.implicit_stat_text':'impl',
        'items.explicit_stat_text':'expl',
        'items.required_level':'levelreq',
        'items.required_intelligence':'intreq',
        'items.required_strength':'strreq',
        'items.required_dexterity':'dexreq',
        'items.base_item':'baseitem',
        'items.inventory_icon':'image_url',

        'weapons.critical_strike_chance_range_text':'crit',
        'weapons.attack_speed_range_text':'aspd',
        'weapons.range_range_text':'range',
        'weapons.physical_damage_max_range_text':'physmax',
        'weapons.physical_damage_min_range_text':'physmin',
        'weapons.fire_damage_max_range_text':'firemax',
        'weapons.fire_damage_min_range_text':'firemin',
        'weapons.cold_damage_max_range_text':'coldmax',
        'weapons.cold_damage_min_range_text':'coldmin',
        'weapons.lightning_damage_max_range_text':'lightmax',
        'weapons.lightning_damage_min_range_text':'lightmin',
        'weapons.chaos_damage_max_range_text':'chaosmax',
        'weapons.chaos_damage_min_range_text':'chaosmin',
        'weapons.elemental_dps_range_text':'eledps',
        'weapons.physical_dps_range_text':'physdps',
##        chaos_dps_range_text??? worth?
        
        'shields.block_range_text':'block',

        'armours.armour_range_text':'armour',
        'armours.energy_shield_range_text':'es',
        'armours.evasion_range_text':'eva',

        'jewels.item_limit':'jewellimit',
        'jewels.radius_html':'jewelradius',

        'flasks.charges_max_range_text':'flaskcharges',
        'flasks.duration_range_text':'flaskduration',
        'flasks.charges_per_use_range_text':'flaskchargesused',
        
}

#image_url is only available if we were lucky enough to scrape it from the db.
def get_image_url(pageName, image_url, is_div_card=False):
        #returns a (best guess) direct url to the main (thumbnail) image for this page.
        query = 'http://pathofexile.gamepedia.com/api.php?action=query&titles={}&prop=pageimages|images&format=json&pithumbsize=10000&imlimit=500'.format(pageName)
        r = requests.get(query)
        r.encoding = 'utf-8'
        rj = r.json()
        pagenum,data = rj['query']['pages'].popitem()
        if int(pagenum)==-1:
                return None
        if 'thumbnail' in data:
                #ezpz we are done
                return data['thumbnail']['source']
        if not image_url and 'images' not in data:
                return None
        # if image_url is defined, we can just use it.
        if not image_url:
                item_name = data['title']
                if is_div_card:
                        title = 'File:{} card art.png'.format(item_name)
                else:
                        title = 'File:{} inventory icon.png'.format(item_name)
                all_images = [x['title'] for x in data['images']]
                all_images.sort(key=lambda a: SequenceMatcher(None, a, title).ratio())

                image_url = all_images[-1]
        
        r = requests.get('http://pathofexile.gamepedia.com/api.php?action=query&titles={}&prop=imageinfo&iiprop=url&format=json'.format(image_url))
        r.encoding = 'utf-8'
        rj = r.json()
        pagenum,data = rj['query']['pages'].popitem()
        if int(pagenum)==-1:
                return None
        if 'imageinfo' in data:
                return data['imageinfo'][0]['url']
        return None

def scrape_unique_items(limit=100000):
        full_results=[]
        fields_to_fetch = list(SKILL_GEM_PROPERTY_MAPPING.values())
        rowindex = 0
        query_limit = 500
        TABLE_SIZE = 9000 #just a guess.
        while rowindex<limit:
                query = 'https://pathofexile.gamepedia.com/api.php?action=cargoquery&format=json&tables=items,weapons,shields,armours,jewels,flasks&join_on=items._pageName=weapons._pageName,items._pageName=shields._pageName,items._pageName=armours._pageName'+\
                        ',items._pageName=jewels._pageName,items._pageName=flasks._pageName'+\
                        '&fields='+','.join(['='.join((k,v)) for k,v in UNIQUE_ITEM_PROPERTY_MAPPING.items()])+'&where=rarity=\'Unique\' AND items._rowID>={} AND items._rowID<{}&group_by=items._pageName&limit={}'.format(rowindex,rowindex+query_limit,query_limit)

                # need to fetch in batches of 500 (the limit for one query)
                # we will use _rowID to do this, continue querying until we get 0 results
                # this isnt 100% safe but it should work unless someone does something to really break the db.
                api_results = []
                for i in range(3):
                        rj=None
                        try:
                                r = requests.get(query)
                                r.encoding = 'utf-8'
                                rj = r.json()
                                api_results = [a['title'] for a in rj['cargoquery']]
                                break
                        except:
                                print(rj)
                                time.sleep(4)
                                #error, trying again.
                if not len(api_results) and rowindex>TABLE_SIZE:
                        break
                for res in api_results:
                        res['impl'] = remove_wiki_formats(html.unescape(res['impl']))
                        res['expl'] = remove_wiki_formats(html.unescape(res['expl']))#.replace('<br>','\n')
                full_results.extend(api_results)
                rowindex+=query_limit
                time.sleep(2)
        # need to call remove_wiki_formats on impl and expl and we should be good2go
##        print('total unique_item results:',len(full_results))
        return full_results

if __name__ == '__main__':
        from pprint import pprint
        print(len(scrape_unique_items()))
##        print('url:',get_image_url('Shimmeron',None))
