import multiprocessing
try:
   multiprocessing.set_start_method('fork', force=True)
   print("forked")
except RuntimeError:
    print("unable to fork!")
    exit()
import re
import sys
import subprocess
import os
import json
import time
from zetanize.zetanize import zetanize
from urllib.parse import urlparse
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

tlds = {'zip', 'llc', 'memorial', 'cpa', 'barclays', 'dz', 'accountant', 'temasek', 'mattel', 'site', 'tt', 'solar', 'ricoh', 'km', 'kyoto', 'haus', 'baidu', 'jetzt', 'flickr', 'ally', 'management', 'xn--pssy2u', 'engineer', 'allstate', 'garden', 'xn--rhqv96g', 'forsale', 'organic', 'estate', 'rentals', 'surgery', 'gmo', 'mt', 'baseball', 'buzz', 'rugby', 'design', 'shangrila', 'delta', 'gt', 'food', 'restaurant', 'redumbrella', 'lundbeck', 'by', 'af', 'dk', 'barefoot', 'page', 'vegas', 'hyundai', 'pn', 'softbank', 'mr', 'review', 'gh', 'afl', 'jp', 'recipes', 'monash', 'airforce', 'ferrero', 'academy', 'hbo', 'tc', 'capital', 'xn--3bst00m', 'shaw', 'leclerc', 'sl', 'xn--42c2d9a', 'me', 'sn', 'voyage', 'citadel', 'ping', 'bi', 'erni', 'seek', 'yun', 'asda', 'shell', 'wiki', 'baby', 'dot', 'eu', 'fly', 'hospital', 'goodyear', 'anz', 'vanguard', 'insurance', 'kr', 'zw', 'tz', 'xn--otu796d', 'travelersinsurance', 'ai', 'photo', 'africa', 'loan', 'otsuka', 'tickets', 'gdn', 'vana', 'sd', 'ie', 'schaeffler', 'tn', 'legal', 'money', 'xn--xkc2dl3a5ee0h', 'iq', 'marshalls', 'voto', 'ae', 'cv', 'lexus', 'sex', 'sexy', 'jewelry', 'sew', 'quest', 'dclk', 'xn--6qq986b3xl', 'dvr', 'discount', 'hotmail', 'yachts', 'toshiba', 'barcelona', 'suzuki', 'hk', 'yokohama', 'email', 'gripe', 'hair', 'aeg', 'bike', 'man', 'skype', 'ing', 'city', 'aarp', 'accenture', 'abc', 'fi', 'cipriani', 'xn--flw351e', 'uz', 'ge', 'natura', 'xn--mgbca7dzdo', 'extraspace', 'events', 'read', 'sharp', 'amazon', 'forum', 'investments', 'beauty', 'prod', 'vn', 'gl', 'click', 'immobilien', 'vote', 'chase', 'netflix', 'smile', 'ss', 'abb', 'silk', 'tattoo', 'jot', 'horse', 'chrome', 'international', 'ifm', 'company', 'hyatt', 'amex', 'xn--j1amh', 'army', 'mma', 'ltd', 'hotels', 'homes', 'vacations', 'do', 'university', 'auto', 'kg', 'stockholm', 'claims', 'film', 'xn--j6w193g', 'wedding', 'versicherung', 'am', 'xn--5tzm5g', 'social', 'im', 'diet', 'tushu', 'eurovision', 'uk', 'george', 'book', 'hamburg', 'faith', 'xn--d1alf', 'theatre', 'open', 'sanofi', 'uno', 'dabur', 'audible', 'lawyer', 'pin', 'sbi', 'holiday', 'sucks', 'citic', 'xn--nyqy26a', 'xn--4dbrk0ce', 'bentley', 'xn--fiq228c5hs', 'physio', 'as', 'nc', 'tienda', 'nab', 'xn--9et52u', 'guru', 'bank', 'business', 'engineering', 'grainger', 'dish', 'diamonds', 'amfam', 'rehab', 'bbc', 'office', 'save', 'analytics', 'sener', 'free', 'xn--fzc2c9e2c', 'ms', 'la', 'delivery', 'kids', 'xn--kprw13d', 'sv', 'lease', 'jio', 'cyou', 'taxi', 'ax', 'itau', 'tiaa', 'ipiranga', 'xn--fiqz9s', 'xn--node', 'network', 'xn--90ais', 'lotto', 'es', 'webcam', 'pw', 'xxx', 'bm', 'xn--80asehdb', 'xn--tckwe', 'compare', 'safety', 'pramerica', 'blog', 'hitachi', 'fox', 'earth', 'center', 'yt', 'actor', 'makeup', 'desi', 'xn--45br5cyl', 'xn--vermgensberatung-pwb', 'luxe', 'pccw', 'best', 'cm', 'cz', 'ren', 'xn--tiq49xqyj', 'jobs', 'kim', 'vision', 'mit', 'jo', 'rip', 'music', 'secure', 'car', 'nissan', 'smart', 'nowruz', 'school', 'xn--ngbe9e0a', 'sh', 'maison', 'lifestyle', 'comcast', 'mls', 'ao', 'brother', 'nissay', 'bond', 'new', 'kz', 'bzh', 'domains', 'lighting', 'lego', 'boehringer', 'attorney', 'barclaycard', 'kred', 'java', 'fish', 'market', 'be', 'cool', 'jeep', 'kerryproperties', 'life', 'sling', 'yamaxun', 'tr', 'travel', 'lamer', 'cologne', 'tatamotors', 'kw', 'drive', 'dental', 'xn--3ds443g', 'flights', 'pioneer', 'hm', 'pf', 'sncf', 'pm', 'progressive', 'mango', 'racing', 'mc', 'cc', 'ky', 'finance', 'si', 'singles', 'axa', 'cooking', 'virgin', 'vlaanderen', 'lancaster', 'mp', 'cloud', 'sarl', 'cn', 'soy', 'productions', 'healthcare', 'xn--9krt00a', 'xn--gk3at1e', 'fido', 'arab', 'immo', 'bt', 'xn--11b4c3d', 'honda', 'scholarships', 'abogado', 'epson', 'xn--o3cw4h', 'aero', 'cd', 'co', 'family', 'ice', 'wolterskluwer', 'skin', 'aaa', 'xn--3e0b707e', 'sandvik', 'ruhr', 'rw', 'sony', 'pub', 'fit', 'coach', 'cars', 'plumbing', 'download', 'poker', 'amica', 'run', 'spa', 'buy', 'hr', 'salon', 'xn--1ck2e1b', 'farmers', 'dad', 'comsec', 'kp', 'monster', 'doctor', 'beats', 'aw', 'ac', 'xn--czru2d', 'grocery', 'med', 'alipay', 'guge', 'surf', 'airbus', 'tours', 'zara', 'xn--c1avg', 'ls', 'goldpoint', 'juniper', 'kuokgroup', 'realtor', 'xn--kcrx77d1x4a', 'aramco', 'fo', 'xn--qxa6a', 'xn--xhq521b', 'love', 'cleaning', 'xn--e1a4c', 'yahoo', 'juegos', 'nr', 'frogans', 'gratis', 'broadway', 'goo', 'xin', 'kh', 'land', 'xihuan', 'citi', 'nokia', 'like', 'dev', 'report', 'xn--h2breg3eve', 'mom', 'olayangroup', 'xn--q7ce6a', 'ad', 'stream', 'latrobe', 'dog', 'gallup', 'press', 'calvinklein', 'vu', 'mw', 'gold', 'cruises', 'athleta', 'commbank', 'gal', 'tube', 'play', 'sz', 'xn--54b7fta0cc', 'career', 'org', 'tax', 'app', 'koeln', 'lu', 'call', 'broker', 'net', 'photography', 'shoes', 'tci', 'boston', 'world', 'bio', 'weber', 'supplies', 'verisign', 'ye', 'rogers', 'dj', 'it', 'security', 'aetna', 'kn', 'energy', 'vi', 'joburg', 'xn--mgbai9azgqp6j', 'xn--gecrj9c', 'samsclub', 'intuit', 'moi', 'xn--pgbs0dh', 'bbva', 'space', 'sport', 'ht', 'media', 'bingo', 'news', 'flir', 'republican', 'accountants', 'stada', 'case', 'fidelity', 'bridgestone', 'fun', 'trading', 'bargains', 'xn--qxam', 'itv', 'realestate', 'zone', 'wien', 'nec', 'ollo', 'gap', 'ventures', 'xn--p1acf', 'emerck', 'date', 'to', 'np', 'dupont', 'ws', 'omega', 'wanggou', 'mg', 'diy', 'sa', 'ceo', 'mtn', 'na', 'kddi', 'xn--j1aef', 'mitsubishi', 'dell', 'author', 'samsung', 'homesense', 'gf', 'durban', 'help', 'ck', 'bar', 'nyc', 'church', 'trv', 'lotte', 'movie', 'tw', 'youtube', 'qa', 'win', 'xn--zfr164b', 'parts', 'men', 'ci', 'jm', 'xn--1qqw23a', 'miami', 'lat', 'americanexpress', 'pics', 'pohl', 'apple', 'furniture', 'tdk', 'windows', 'latino', 'statefarm', 'auspost', 'contact', 'democrat', 'nike', 'pars', 'select', 'schwarz', 'vip', 'consulting', 'voting', 'edeka', 'lipsy', 'stc', 'creditcard', 'je', 'williamhill', 'prime', 'courses', 'xn--ygbi2ammx', 'dunlop', 'wine', 'motorcycles', 'landrover', 'xn--s9brj9c', 'ro', 'credit', 'clinique', 'playstation', 'gi', 'xn--hxt814e', 'bz', 'deloitte', 'coupon', 'saxo', 'prof', 'bet', 'mo', 'praxi', 'lasalle', 'homedepot', 'al', 'map', 'edu', 'soccer', 'il', 'er', 'vg', 'xn--mgb9awbf', 'bible', 'paris', 'xn--imr513n', 'got', 'gucci', 'orange', 'archi', 'eat', 'netbank', 'ug', 'schmidt', 'nico', 'ag', 'construction', 'feedback', 'xn--cck2b3b', 'flowers', 'xn--mgberp4a5d4ar', 'frl', 'xn--cg4bki', 'bbt', 'xn--80aqecdr1a', 'mobile', 'avianca', 'bh', 'red', 'pl', 'xn--9dbq2a', 'channel', 'ftr', 'software', 'place', 'xn--mgbgu82a', 'xn--w4r85el8fhu5dnra', 'exposed', 'yandex', 'agakhan', 'bosch', 'globo', 'staples', 'capetown', 'beer', 'frontier', 'va', 'caravan', 'gov', 'uy', 'abudhabi', 'arpa', 'search', 'xn--c2br7g', 'tl', 'yodobashi', 'vet', 'mz', 'lacaixa', 'target', 'villas', 'rexroth', 'hkt', 'tools', 'asia', 'contractors', 'viking', 'xn--mgbc0a9azcg', 'pro', 'ril', 'art', 'coupons', 'kpmg', 'xn--vuq861b', 'dds', 'meme', 'jnj', 'nz', 'website', 'tirol', 'abbvie', 'condos', 'lplfinancial', 'sina', 'xn--czr694b', 'unicom', 'gq', 'americanfamily', 'careers', 'xn--wgbl6a', 'bestbuy', 'eg', 'xn--fpcrj9c3d', 'gmx', 'properties', 'cl', 'bharti', 'ubank', 'wtc', 'lk', 'mx', 'xn--lgbbat1ad8j', 'xn--3hcrj9c', 'corsica', 'rs', 'hu', 'bayern', 'adult', 'xn--h2brj9c', 'wtf', 'florist', 'codes', 'xn--mgbtx2b', 'xn--mgbah1a3hjkrd', 'shiksha', 'lol', 'theater', 'xn--czrs0t', 'nexus', 'xn--unup4y', 'viajes', 'gbiz', 'xn--45brj9c', 'limited', 'sbs', 'xn--gckr3f0f', 'bo', 'ch', 'ford', 'eus', 'ninja', 'hosting', 'education', 'town', 'bot', 'catholic', 'nfl', 'ski', 'scb', 'able', 'st', 'bom', 'rest', 'charity', 'au', 'how', 'ke', 'supply', 'xn--6frz82g', 'pnc', 'xn--mgbx4cd0ab', 'agency', 'xn--4gbrim', 'dating', 'xn--i1b6b1a6a2e', 'xn--jvr189m', 'ba', 'bb', 'ne', 'audi', 'xn--80aswg', 'glass', 'plus', 'kpn', 'xn--mgbpl2fh', 'xn--eckvdtc9d', 'ggee', 'vc', 'gy', 'ooo', 'xn--ngbrx', 'blockbuster', 'trade', 'toys', 'swiss', 'xn--mgbt3dhd', 'bnpparibas', 'toyota', 'digital', 'mini', 'kfh', 'xn--fjq720a', 'tkmaxx', 'xn--qcka1pmc', 'neustar', 'viva', 'apartments', 'aol', 'xn--io0a7i', 'visa', 'nrw', 'tel', 'ott', 'allfinanz', 'dhl', 'xfinity', 'phone', 'om', 'fishing', 'xn--8y0a063a', 'aig', 'data', 'cash', 'nba', 'enterprises', 'community', 'college', 'mn', 'br', 'hermes', 'locker', 'shop', 'game', 'works', 'booking', 'show', 'philips', 'ph', 'hiv', 'ads', 'cal', 'cfa', 'guide', 'lt', 'ua', 'meet', 'ngo', 'xn--5su34j936bgsg', 'bf', 'kindle', 'casa', 'xn--2scrj9c', 'xn--p1ai', 'tech', 'clothing', 'guardian', 'chat', 'xn--nqv7fs00ema', 'pa', 'istanbul', 'xn--55qx5d', 'associates', 'basketball', 'dentist', 'xn--g2xx48c', 'hot', 'xn--vhquv', 'xn--mix891f', 'woodside', 'canon', 'xbox', 'dealer', 'de', 'godaddy', 'xn--mgbi4ecexp', 'uol', 'xn--cckwcxetd', 'nextdirect', 'cw', 'fail', 'boats', 'style', 'thd', 'financial', 'cat', 'pwc', 'bostik', 'gift', 'xn--mgba3a4f16a', 'xn--vermgensberater-ctb', 'farm', 'cx', 'reisen', 'aq', 'partners', 'tips', 'cafe', 'moe', 'prudential', 'fairwinds', 'walter', 'luxury', 'bauhaus', 'crs', 'gd', 'gw', 'here', 'pharmacy', 'int', 'th', 'pt', 'za', 'oracle', 'loans', 'su', 'richardli', 'law', 'msd', 'shia', 'locus', 'protection', 'banamex', 'hdfcbank', 'tvs', 'foundation', 'taipei', 'rent', 'anquan', 'name', 'nowtv', 'rodeo', 'gu', 'ml', 'camp', 'quebec', 'host', 'ieee', 'ist', 'io', 'xn--mgbbh1a', 'circle', 'sb', 'sc', 'whoswho', 'gr', 'green', 'menu', 'gallery', 'fk', 'xn--rovu88b', 'hughes', 'berlin', 'gn', 'pet', 'akdn', 'discover', 'porn', 'fan', 'firmdale', 'mint', 'xn--l1acc', 'cards', 'ee', 'industries', 'chanel', 'sandvikcoromant', 've', 'cfd', 'olayan', 'catering', 'post', 'tatar', 'cy', 'md', 'sk', 'blue', 'google', 'storage', 'id', 'kerrylogistics', 'onl', 'eco', 'icu', 'tm', 'cr', 'moto', 'reise', 'airtel', 'politie', 'box', 'fans', 'ir', 'fujitsu', 'giving', 'pr', 'zero', 'cab', 'xn--fzys8d69uvgm', 'fyi', 'xn--45q11c', 'alstom', 'kitchen', 'se', 'ar', 'xn--xkc2al3hye2a', 'xyz', 'fage', 'store', 'video', 'ec', 'gp', 'observer', 'sale', 'day', 'kiwi', 'osaka', 'sj', 'xn--mxtq1m', 'nagoya', 'firestone', 'christmas', 'jcb', 'rsvp', 'my', 'xn--jlq480n2rg', 'institute', 'esq', 'mov', 'imamat', 'rocks', 'inc', 'obi', 'gay', 'tg', 'xn--ses554g', 'nf', 'sx', 'hiphop', 'krd', 'tennis', 'gifts', 'tunes', 'realty', 'goog', 'irish', 'mckinsey', 'xn--t60b56a', 'travelers', 'ca', 'cisco', 'limo', 're', 'docs', 'technology', 'audio', 'joy', 'team', 'mq', 'cf', 'xn--mgbaam7a8h', 'winners', 'xn--fhbei', 'xn--mgbbh1a71e', 'deal', 'is', 'sydney', 'xn--mgbcpq6gpa1a', 'mk', 'tjmaxx', 'jmp', 'sg', 'lilly', 'lc', 'li', 'jll', 'arte', 'xn--yfro4i67o', 'services', 'wf', 'creditunion', 'exchange', 'nra', 'mobi', 'ismaili', 'casino', 'cymru', 'xn--q9jyb4c', 'talk', 'support', 'mba', 'online', 'photos', 'rio', 'lb', 'sas', 'xn--fiq64b', 'work', 'song', 'pictet', 'xn--80ao21a', 'blackfriday', 'zuerich', 'pg', 'today', 'vig', 'guitars', 'helsinki', 'dnp', 'android', 'lr', 'com', 'tui', 'no', 'imdb', 'tab', 'walmart', 'xn--mgba7c0bbn0a', 'statebank', 'science', 'link', 'cg', 'fedex', 'wow', 'fitness', 'ly', 'group', 'us', 'ikano', 'dvag', 'volvo', 'gallo', 'srl', 'marriott', 'ntt', 'ki', 'xn--mgba3a3ejt', 'xn--55qw42g', 'merckmsd', 'club', 'hisamitsu', 'llp', 'amsterdam', 'trust', 'ga', 'systems', 'alibaba', 'xn--3pxu8k', 'xn--mgbayh7gpa', 'bid', 'jpmorgan', 'xn--kput3i', 'taobao', 'cruise', 'party', 'qpon', 'solutions', 'lifeinsurance', 'care', 'ng', 'crown', 'lamborghini', 'xn--h2brj9c8c', 'xn--ngbc5azd', 'py', 'hn', 'tk', 'panasonic', 'saarland', 'london', 'kerryhotels', 'teva', 'navy', 'gives', 'td', 'capitalone', 'house', 'vivo', 'gg', 'gmail', 'xn--mk1bu44c', 'chintai', 'rich', 'ubs', 'mm', 'futbol', 'mv', 'nl', 'xerox', 'bcg', 'markets', 'xn--90ae', 'studio', 'hdfc', 'gs', 'games', 'wed', 'aco', 'so', 'safe', 'sr', 'aws', 'vin', 'hsbc', 'ma', 'norton', 'biz', 'gent', 'tf', 'insure', 'cern', 'gb', 'top', 'living', 'homegoods', 'pictures', 'bofa', 'fresenius', 'lidl', 'directory', 'degree', 'pink', 'lpl', 'mu', 'xn--wgbh1c', 'fj', 'dance', 'training', 'football', 'mtr', 'okinawa', 'band', 'ni', 'mil', 'reliance', 'nhk', 'bms', 'pru', 'pk', 'infiniti', 'seven', 'hangout', 'xn--w4rs40l', 'bloomberg', 'ru', 'cheap', 'ibm', 'zm', 'xn--rvc1e0am3e', 'watches', 'in', 'bw', 'golf', 'auction', 'gop', 'gm', 'now', 'cbre', 'microsoft', 'weatherchannel', 'forex', 'azure', 'pe', 'ericsson', 'xn--b4w605ferd', 'museum', 'study', 'et', 'bv', 'graphics', 'mormon', 'sfr', 'weather', 'madrid', 'ltda', 'nu', 'brussels', 'moscow', 'dm', 'bs', 'tmall', 'vodka', 'clubmed', 'global', 'lefrak', 'tj', 'gea', 'marketing', 'you', 'ryukyu', 'dtv', 'cbn', 'health', 'xn--fiqs8s', 'hockey', 'moda', 'bmw', 'sohu', 'origins', 'stcgroup', 'deals', 'cam', 'bd', 'mlb', 'computer', 'lincoln', 'datsun', 'shopping', 'cu', 'gle', 'equipment', 'scot', 'xn--d1acj3b', 'swatch', 'zappos', 'xn--90a3ac', 'xn--ogbpf8fl', 'fm', 'wales', 'az', 'mortgage', 'xn--fct429k', 'black', 'bradesco', 'clinic', 'tires', 'radio', 'weibo', 'next', 'fr', 'room', 'fire', 'genting', 'coop', 'xn--clchc0ea0b2g2a9gcd', 'expert', 'tv', 'pid', 'tjx', 'direct', 'melbourne', 'watch', 'build', 'sky', 'one', 'foo', 'jaguar', 'redstone', 'sap', 'nikon', 'yoga', 'abbott', 'cba', 'xn--efvy88h', 'ps', 'at', 'ferrari', 'promo', 'bg', 'reit', 'kaufen', 'lgbt', 'dubai', 'sy', 'xn--nqv7f', 'tokyo', 'jprs', 'lanxess', 'phd', 'fund', 'live', 'ovh', 'sm', 'camera', 'lds', 'xn--y9a3aq', 'seat', 'fast', 'bj', 'ink', 'aquarelle', 'schule', 'boutique', 'mh', 'wme', 'coffee', 'country', 'toray', 'xn--80adxhks', 'gmbh', 'spot', 'cricket', 'wang', 'sakura', 'xn--kpry57d', 'xn--mgbab2bd', 'shouji', 'komatsu', 'info', 'bn', 'boo', 'alsace', 'xn--30rr7y', 'pay', 'property', 'total', 'autos', 'ups', 'bing', 'pfizer', 'express', 'pizza', 'cuisinella', 'fashion', 'weir', 'maif', 'repair', 'reviews', 'bcn', 'holdings', 'xn--bck1b9a5dre4c', 'rwe', 'final', 'ong', 'builders', 'kosher', 'star', 'kia', 'lv', 'icbc'}

tlds = list(tlds)
tlds.sort(reverse=True, key=len)

def valid_domain(domain):
    tld_count = 0
    preserved_domain = domain
    domain = domain.lower()
    for tld in tlds:
        rightmost_tld = '.' + tld
        middle_tld = '.' + tld + '.'
        if rightmost_tld in domain and rightmost_tld[-1] == domain[-1] and rightmost_tld[-2] == domain[-2]:
            domain = domain.replace(tld,"")
            tld_count += 1
        if middle_tld in domain:
            domain = domain.replace(tld,"")
            tld_count += 1
    if preserved_domain.count('.') == tld_count and tld_count != 0 and preserved_domain.split(".")[0] != "":
        return True
    else:
        return False

def valid_subdomain(subdomain):
    tld_count = 0
    preserved_subdomain = subdomain
    subdomain = subdomain.lower()
    for tld in tlds:
        rightmost_tld = '.' + tld
        middle_tld = '.' + tld + '.'
        if rightmost_tld in subdomain and rightmost_tld[-1] == subdomain[-1] and rightmost_tld[-2] == subdomain[-2]:
            subdomain = subdomain.replace(tld,"")
            tld_count += 1
        if middle_tld in subdomain:
            subdomain = subdomain.replace(tld,"")
            tld_count += 1
    if preserved_subdomain.count('.') > tld_count and tld_count != 0 and preserved_subdomain.split(".")[0] != "":
        return True
    else:
        return False

def get_domain_from_subdomain(subdomain):
    domain = ""
    tld_count = 0
    subdomain = subdomain.lower()
    for tld in tlds:
        rightmost_tld = '.' + tld
        middle_tld = '.' + tld + '.'
        if rightmost_tld in subdomain and rightmost_tld[-1] == subdomain[-1] and rightmost_tld[-2] == subdomain[-2]:
            tld_count += 1
        if middle_tld in subdomain:
            tld_count += 1
    regex_to_match = "^(.*?" + ("\..*?" * (subdomain.count(".") - (tld_count + 1) )) + ")\."
    domain = re.sub(regex_to_match,"",subdomain)
    return domain

def domain_list_prepare():
    assets = set()
    domains = set()
    with open('./../../assets_of_target_and_its_acquisitions') as file:
        for asset in file:
            asset = asset.replace("\n","")
            if asset != "":
                assets.add(asset)
    with open('./../../reverse_whois_output') as file:
        for asset in file:
            asset = asset.replace("\n","")
            if asset != "":
                assets.add(asset)
    with open('./../../IP_based_reverse_dns_output') as file:
        for asset in file:
            asset = asset.replace("\n","")
            if asset != "":
                assets.add(asset)
    with open('./../../ssl_certificate_grabbing_output') as file:
        for asset in file:
            asset = asset.replace("\n","")
            if asset != "":
                assets.add(asset)
    with open('./../../tld_enum_output') as file:
        for asset in file:
            asset = asset.replace("\n","")
            if asset != "":
                assets.add(asset)
    for asset in assets:
        if valid_domain(asset):
            domains.add(asset)
        elif valid_subdomain(asset):
            domains.add(get_domain_from_subdomain(asset))
    
    return list(domains)

collected_domains = set()
# try:
#     with open("domains_which_sources_we_have_collected") as collected_domains_file:
#         for domain in collected_domains_file:
#             domain = domain.replace("\n","")
#             collected_domains.add(domain)
# except:
#     pass


proxies = ["self"]
for f_or_d in os.listdir('/home/deus/documents'):
    if "proxychains" in f_or_d:
        proxies.append(f_or_d)

manager = multiprocessing.Manager()
used_proxies_across_processes = manager.list()
counter = multiprocessing.Value('i',1)
domains_and_their_sources = manager.dict()
forms = manager.list()
forms_urls_output_lock = multiprocessing.Lock()
mv_lock = multiprocessing.Lock()
in_extraction = False

domains = list()
meticulous_check = True

keywords_we_find_sources_for = set()

pages_with_forms_count = 0
for f_or_d in os.listdir('./'):
    if f"pages_with_forms" in f_or_d:
        pages_with_forms_count += 1


parser = argparse.ArgumentParser(description="Run feroxbuster with specified URL, request file, and methods.")
parser.add_argument("-f", "--file-type", required=False, help="The target URL. or file of target URLS")
parser.add_argument("-t", "--target-type", required=False, help="The target URL. or file of target URLS")
parser.add_argument("-c", "--contains", required=False, help="The target URL. or file of target URLS")
parser.add_argument("-l", "--limit", required=False, help="The target URL. or file of target URLS")
args = parser.parse_args()


if "subdomains_with_authentication" in args.file_type:
    with open('./../../subdomains_with_authentication') as file:
        for domain in file:
            domain = domain.replace("\n","")
            domains.append(domain)
            # domains.append(domain.replace("www.",""))

    # for i in range(2, len(sys.argv)):
    if "all" == args.target_type:
        with open('./../../subdomains_with_authentication') as file:
            for domain in file:
                domain = domain.replace("\n","")
                keywords_we_find_sources_for.add(domain)
    elif "*" in args.target_type:
        args.target_type = args.target_type.replace("*","")
        with open('./../../subdomains_with_authentication') as file:
            for domain in file:
                domain = domain.replace("\n","")
                if args.target_type in domain:
                    keywords_we_find_sources_for.add(domain)
    else:
        keywords_we_find_sources_for.add(args.target_type)
elif "_download" in args.file_type:

    if "all" == args.target_type:
        with open('./../../collected_domains.txt') as file:
            for domain in file:
                domain = domain.replace("\n","")
                domains.append(domain)
                # domains.append(domain.replace("www.",""))
    elif "subtarget" == args.target_type:
        with open('./../all_subtarget_domains.txt') as file:
            for hostname in file:
                # url = url.replace("\n","")
                # hostname = urlparse(url).hostname
                hostname = hostname.strip()
                domains.append(hostname)
                # domains.append(hostname.replace("www.",""))
    elif "*" in args.target_type:
        args.target_type = args.target_type.replace("*","")

        with open('./../../collected_domains.txt') as file:
            for domain in file:
                domain = domain.replace("\n","")
                if args.target_type in domain:
                    domains.append(domain)
    else:
        if os.path.isfile(args.target_type):
            with open(args.target_type, 'r') as f:
                for domain in f:
                    domain = domain.strip()
                    domains.append(domain)

        else:
            domains.append(args.target_type)
        # domains.append(args.target_type.replace("www.",""))
    
    # for i in range(3, len(sys.argv)):
    #     keywords_we_find_sources_for.add(sys.argv[i])
    
    for contain in args.contains.split(","):
        keywords_we_find_sources_for.add(contain)
    
    meticulous_check = False
elif "html_based_search" in args.file_type:

    if "all" == args.target_type:
        with open('./../../collected_domains.txt') as file:
            for domain in file:
                domain = domain.replace("\n","")
                domains.append(domain)
                # domains.append(domain.replace("www.",""))
    elif "subtarget" == args.target_type:
        with open('./../all_subtarget_domains.txt') as file:
            for hostname in file:
                # url = url.replace("\n","")
                # hostname = urlparse(url).hostname
                hostname = hostname.strip()
                domains.append(hostname)
                # domains.append(hostname.replace("www.",""))
    elif "*" in args.target_type:
        args.target_type = args.target_type.replace("*","")

        with open('./../../collected_domains.txt') as file:
            for domain in file:
                domain = domain.replace("\n","")
                if args.target_type in domain:
                    domains.append(domain)
                    # domains.append(domain.replace("www.",""))
    else:
        domains.append(args.target_type)
        # domains.append(args.target_type.replace("www.",""))
    
    for contain in args.contains.split(","):
        keywords_we_find_sources_for.add(contain)
    
    meticulous_check = False
# else:
#     # domains = list(set(domain_list_prepare()) - collected_domains)
#     with open('./../../collected_domains.txt') as file:
#         for domain in file:
#             domain = domain.replace("\n","")
#             domains.append(domain)

#     for i in range(1, len(sys.argv)):
#         if "all" == sys.argv[i]:
#             with open('./../../collected_domains.txt') as file:
#                 for domain in file:
#                     domain = domain.replace("\n","")
#                     keywords_we_find_sources_for.add(domain)
#         elif "*" in sys.argv[i]:
#             sys.argv[i] = sys.argv[i].replace("*","")
#             with open('./../../collected_domains.txt') as file:
#                 for domain in file:
#                     domain = domain.replace("\n","")
#                     if sys.argv[i] in domain:
#                         keywords_we_find_sources_for.add(domain)
#         else:
#             keywords_we_find_sources_for.add(sys.argv[i])

domains = list(set(domains))
domains_len = len(domains)
keywords_we_find_sources_for = list(keywords_we_find_sources_for)

# if valid_domain(keywords_we_find_sources_for[0]):
#     main_domain = keywords_we_find_sources_for[0]
# elif valid_subdomain(keywords_we_find_sources_for[0]):
#     main_domain = get_domain_from_subdomain(keywords_we_find_sources_for[0])

# def find_all_ending_index_of_subdomains_of_desired_subdomain_or_domain(content, desired_domain):
#     last_ending_index = 0
#     ending_indices = list()
#     sub_reg = "[a-zA-Z0-9-._]+\.(desireddomain.tld)".replace("desireddomain.tld",desired_domain)
#     while True:
#         match = re.search(sub_reg,content[last_ending_index:])
#         if match == None: return ending_indices
#         last_ending_index += match.end()
#         ending_indices.append(last_ending_index)

# def find_all_ending_index_of_desired_domain(content, desired_domain):
#     last_ending_index = 0
#     ending_indices = list()
#     while True:
#         match = re.search(desired_domain,content[last_ending_index:])
#         if match == None: return ending_indices
#         last_ending_index += match.end()
#         ending_indices.append(last_ending_index)



# with open('collected_domains.txt') as domains_from_file:
#     for domain in domains_from_file:
#         domain = domain.replace("\n","")
#         domains.append(domain)

sources_dir = os.getcwd()
wayback_dir = ""
apk_dir = ""
burp_dir = ""
if "_download" in args.file_type:
    # fuzz_dir = ""

    if not os.path.exists(sources_dir):
        os.makedirs(sources_dir)
        os.makedirs(sources_dir + '/source1')
        
        with open(f'{sources_dir}/source1/arguments_used_for_this_source.log', "a") as log_file:
            # log_file.write(f'{" ".join(sys.argv[2:])}' + "\n")
            log_file.write(f'{" ".join(str(logging.info("Arguments: %s", vars(args))))}' + "\n")


        wayback_dir = sources_dir + '/source1/wayback'
        apk_dir = sources_dir + '/source1/apk'
        burp_dir = sources_dir + '/source1/burp'
        # fuzz_dir = sources_dir + '/source1/fuzz'
    else:
        dir_count = len([name for name in os.listdir(sources_dir) if os.path.isdir(os.path.join(sources_dir, name)) and name.startswith("source")]) + 1
        os.makedirs(f'{sources_dir}/source{dir_count}')

        with open(f'{sources_dir}/source{dir_count}/arguments_used_for_this_source.log', "a") as log_file:
            log_file.write(f'{" ".join(str(logging.info("Arguments: %s", vars(args))))}' + "\n")
        
        wayback_dir = f'{sources_dir}/source{dir_count}/wayback'
        apk_dir = f'{sources_dir}/source{dir_count}/apk'
        burp_dir = f'{sources_dir}/source{dir_count}/burp'
        # fuzz_dir = f'{sources_dir}/source{dir_count}/fuzz'

    os.makedirs(wayback_dir)
    # os.makedirs(apk_dir)
    # os.makedirs(burp_dir)

def get_directory_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                if os.path.isfile(fp):
                    total_size += os.path.getsize(fp)
            except FileNotFoundError:
                continue  # Skip if file was deleted during scan
    return total_size

def source_identifier(domain):
    global domains_and_their_sources
    global meticulous_check
    global domains
    global domains_len
    global counter
    global proxies
    global used_proxies_across_processes
    global keywords_we_find_sources_for
    global manager
    global wayback_dir
    global forms
    global forms_urls_output_lock
    global pages_with_forms_count
    global mv_lock
    global in_extraction

    while True:
        if in_extraction:
            time.sleep(10)
            continue
        
        break
    
    
    while True:
        try:
            proxy = list(set(proxies) - set(used_proxies_across_processes))[0]
            used_proxies_across_processes.append(proxy)
            break
        except:
            time.sleep(2)
    
    failure_count = 0
    index_of_domain = domains.index(domain)

    # log_file = open("logfile.log", "a")
    # log_file.write(proxy + " here1" + "\n")
    # log_file.close()
    timeout_count = 0

    if proxy == "self":
        time.sleep(10)
    else:
        time.sleep(9)

    while True:
        if proxy == "self":
            try:
                if "js_download" in args.file_type:
                    # subprocess.run(f' bash -c \' waymore -i {domain} -mode R -r 2 -p 5 -xcc -l 0 -url-filename -c ~/documents/js_resources_config.yml &> waymore_output_{index_of_domain}.txt \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True, timeout=8000)
                    with open(f'waymore_output_{index_of_domain}.txt', 'w') as outfile:
                        subprocess.run(
                            [
                                'waymore',
                                '-i', domain,
                                '-mode', 'R',
                                '-r', '2',
                                '-p', '5',
                                '-xcc',
                                '-l', args.limit,
                                '-url-filename',
                                '-c', '/home/deus/documents/js_resources_config.yml'  # ~ is not expanded in shell=False
                            ],
                            stdin=subprocess.DEVNULL,
                            stdout=outfile,
                            stderr=subprocess.STDOUT,
                            text=True,
                            timeout=8000
                        )
                    
                elif "html_download" in args.file_type:
                    # subprocess.run(f' bash -c \' waymore -i {domain} -mode R -r 2 -p 5 -xcc -l 0 -url-filename -c ~/documents/js_resources_config.yml &> waymore_output_{index_of_domain}.txt \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True, timeout=8000)
                    with open(f'waymore_output_{index_of_domain}.txt', 'w') as outfile:
                        subprocess.run(
                            [
                                'waymore',
                                '-i', domain,
                                '-mode', 'R',
                                '-r', '2',
                                '-p', '5',
                                '-xcc',
                                '-l', args.limit,
                                '-url-filename',
                                '-c', '/home/deus/documents/html_resources_config.yml'  # ~ is not expanded in shell=False
                            ],
                            stdin=subprocess.DEVNULL,
                            stdout=outfile,
                            stderr=subprocess.STDOUT,
                            text=True,
                            timeout=8000
                        )
                    
                    # subprocess.run(f'/bin/bash -c \'grep -F -a -e ".yaml" -e ".yml" -e ".json" -e ".js" ~/.config/waymore/results/{domain}/waymore.txt > ~/.config/waymore/results/{domain}/source_links.txt \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True)
                    # time.sleep(10)
                    # subprocess.run(f' bash -c \' waymore -i ~/.config/waymore/results/{domain}/source_links.txt -mode R -r 2 -p 5 -xcc -l -10000 -url-filename -c ~/documents/js_resources_config.yml -oR ~/.config/waymore/results/{domain} \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True, timeout=8000)
                elif "html_based_search" in args.file_type:
                    # subprocess.run(f' bash -c \' waymore -i {domain} -mode B -ci m -r 2 -p 5 -xcc -l -5000 -url-filename -c ~/documents/html_resources_config.yml &> waymore_output_{index_of_domain}.txt \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True, timeout=8000)
                    with open(f'waymore_output_{index_of_domain}.txt', 'w') as outfile:
                        subprocess.run(
                            [
                                'waymore',
                                '-i', domain,
                                '-mode', 'B',
                                '-ci', 'm',
                                '-r', '2',
                                '-p', '5',
                                '-xcc',
                                '-l', '-5000',
                                '-url-filename',
                                '-c', '/home/deus/documents/html_resources_config.yml'  # don't use ~ in shell=False
                            ],
                            stdin=subprocess.DEVNULL,
                            stdout=outfile,
                            stderr=subprocess.STDOUT,
                            text=True,
                            timeout=8000
                        )

                    # subprocess.run(f'/bin/bash -c \'grep -F -a -e ".yaml" -e ".yml" -e ".json" -e ".js" ~/.config/waymore/results/{domain}/waymore.txt > ~/.config/waymore/results/{domain}/source_links.txt \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True)
                    # time.sleep(10)
                    # subprocess.run(f' bash -c \' waymore -i ~/.config/waymore/results/{domain}/waymore.txt -mode R -r 2 -p 5 -xcc -l -5000 -url-filename -c ~/documents/html_resources_config.yml -oR ~/.config/waymore/results/{domain} \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True, timeout=8000)
                else:
                    # subprocess.run(f' bash -c \' waymore -i  -mode B -r 2 -p 5 -xcc -c /home/deus/documents/html_resources_config.yml &> waymore_output_{index_of_domain}.txt \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True, timeout=2000)
                    with open(f'waymore_output_{index_of_domain}.txt', 'w') as outfile:
                        subprocess.run(
                            [
                                'waymore',
                                '-i', '',  # Empty input value; you may want to fill this in
                                '-mode', 'B',
                                '-r', '2',
                                '-p', '5',
                                '-xcc',
                                '-c', '/home/deus/documents/html_resources_config.yml'
                            ],
                            stdin=subprocess.DEVNULL,
                            stdout=outfile,
                            stderr=subprocess.STDOUT,
                            text=True,
                            timeout=2000
                        )

                # else:
                #     subprocess.run(f' bash -c \' waymore -i {domain} -mode B -r 2 -p 3 -xcc &> waymore_output_{index_of_domain}.txt \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True, timeout=2000)

            except subprocess.TimeoutExpired:
                timeout_count += 1
        else:
            try:
                if "js_download" in args.file_type:
                    # subprocess.run(f' bash -c \' proxychains4 -f /home/deus/documents/{proxy} -q waymore -i {domain} -mode R -r 2 -p 5 -xcc -l 0 -url-filename -c ~/documents/js_resources_config.yml &> waymore_output_{index_of_domain}.txt \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True, timeout=8000)
                    with open(f'waymore_output_{index_of_domain}.txt', 'w') as outfile:
                        subprocess.run(
                            [
                                'proxychains4',
                                '-f', f'/home/deus/documents/{proxy}',
                                '-q',
                                'waymore',
                                '-i', domain,
                                '-mode', 'R',
                                '-r', '2',
                                '-p', '5',
                                '-xcc',
                                '-l', args.limit,
                                '-url-filename',
                                '-c', '/home/deus/documents/js_resources_config.yml'  # Expanded ~ manually
                            ],
                            stdin=subprocess.DEVNULL,
                            stdout=outfile,
                            stderr=subprocess.STDOUT,
                            text=True,
                            timeout=8000
                        )
                    
                elif "html_download" in args.file_type:
                    # subprocess.run(f' bash -c \' proxychains4 -f /home/deus/documents/{proxy} -q waymore -i {domain} -mode R -r 2 -p 5 -xcc -l 0 -url-filename -c ~/documents/js_resources_config.yml &> waymore_output_{index_of_domain}.txt \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True, timeout=8000)
                    with open(f'waymore_output_{index_of_domain}.txt', 'w') as outfile:
                        subprocess.run(
                            [
                                'proxychains4',
                                '-f', f'/home/deus/documents/{proxy}',
                                '-q',
                                'waymore',
                                '-i', domain,
                                '-mode', 'R',
                                '-r', '2',
                                '-p', '5',
                                '-xcc',
                                '-l', args.limit,
                                '-url-filename',
                                '-c', '/home/deus/documents/html_resources_config.yml'  # Expanded ~ manually
                            ],
                            stdin=subprocess.DEVNULL,
                            stdout=outfile,
                            stderr=subprocess.STDOUT,
                            text=True,
                            timeout=8000
                        )
                    
                    # subprocess.run(f'/bin/bash -c \'grep -F -a -e ".yaml" -e ".yml" -e ".json" -e ".js" ~/.config/waymore/results/{domain}/waymore.txt > ~/.config/waymore/results/{domain}/source_links.txt \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True)
                    # time.sleep(10)
                    # subprocess.run(f' bash -c \' proxychains4 -f /home/deus/documents/{proxy} -q waymore -i ~/.config/waymore/results/{domain}/source_links.txt -mode R -r 2 -p 5 -xcc -l -5000 -url-filename -c ~/documents/js_resources_config.yml -oR ~/.config/waymore/results/{domain} \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True, timeout=8000)
                
                elif "html_based_search" in args.file_type:
                    # subprocess.run(f' bash -c \' proxychains4 -f /home/deus/documents/{proxy} -q waymore -i {domain} -mode B -ci m -r 2 -p 5 -xcc -l -10000 -url-filename -c ~/documents/html_resources_config.yml &> waymore_output_{index_of_domain}.txt \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True, timeout=8000)
                    with open(f'waymore_output_{index_of_domain}.txt', 'w') as outfile:
                        subprocess.run(
                            [
                                'proxychains4',
                                '-f', f'/home/deus/documents/{proxy}',
                                '-q',
                                'waymore',
                                '-i', domain,
                                '-mode', 'B',
                                '-ci', 'm',
                                '-r', '2',
                                '-p', '5',
                                '-xcc',
                                '-l', '-10000',
                                '-url-filename',
                                '-c', '/home/deus/documents/html_resources_config.yml'  # '~' manually expanded
                            ],
                            stdin=subprocess.DEVNULL,
                            stdout=outfile,
                            stderr=subprocess.STDOUT,
                            text=True,
                            timeout=8000
                        )

                    # subprocess.run(f'/bin/bash -c \'grep -F -a -e ".yaml" -e ".yml" -e ".json" -e ".js" ~/.config/waymore/results/{domain}/waymore.txt > ~/.config/waymore/results/{domain}/source_links.txt \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True)
                    # time.sleep(10)
                    # subprocess.run(f' bash -c \' proxychains4 -f /home/deus/documents/{proxy} -q waymore -i ~/.config/waymore/results/{domain}/waymore.txt -mode R -r 2 -p 5 -xcc -l -5000 -url-filename -c ~/documents/html_resources_config.yml -oR ~/.config/waymore/results/{domain} \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True, timeout=8000)
                else:
                    # subprocess.run(f' bash -c \' proxychains4 -f /home/deus/documents/{proxy} -q waymore -i {domain} -mode B -r 2 -p 5 -xcc -c /home/deus/documents/html_resources_config.yml &> waymore_output_{index_of_domain}.txt \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True, timeout=2000)
                    with open(f'waymore_output_{index_of_domain}.txt', 'w') as outfile:
                        subprocess.run(
                            [
                                'proxychains4',
                                '-f', f'/home/deus/documents/{proxy}',
                                '-q',
                                'waymore',
                                '-i', domain,
                                '-mode', 'B',
                                '-r', '2',
                                '-p', '5',
                                '-xcc',
                                '-c', '/home/deus/documents/html_resources_config.yml'
                            ],
                            stdin=subprocess.DEVNULL,
                            stdout=outfile,
                            stderr=subprocess.STDOUT,
                            text=True,
                            timeout=2000
                        )

                
            except subprocess.TimeoutExpired:
                timeout_count += 1
        
        condition_of_waymore_output = subprocess.run(f'/bin/bash -c \'tail -n 100 waymore_output_{index_of_domain}.txt \' ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True).stdout
        if "100.0% Complete" in condition_of_waymore_output or "No archived responses were found" in condition_of_waymore_output or timeout_count == 2:
            # domains_which_sources_we_have_collected = open("domains_which_sourcesfasdfsdljflsk rdddd_we_have_collected", "a")
            # domains_which_sources_we_have_collected.write(domain + "\n")
            # domains_which_sources_we_have_collected.close()
            used_proxies_across_processes.remove(proxy)
            break
        
        failure_count += 1
        error_count = open("error_count", "a")
        error_count.write(proxy + " " + str(domain) + " "  + str(failure_count) + "\n")
        error_count.close()
        if failure_count > 2:
            used_proxies_across_processes.remove(proxy)
            break
        time.sleep(60)
    
    subprocess.run(f'/bin/bash -c \'rm waymore_output_{index_of_domain}.txt \' ', shell=True)

    def is_the_interested_domain_in_content(content, desired_domain):
        last_ending_index_of_subdomains_of_desired_subdomain_or_domain = 0
        last_ending_index_of_desired_domain = 0
        ending_indices = list()
        sub_reg = "[a-zA-Z0-9-._]+\.(desireddomain.tld)".replace("desireddomain.tld",desired_domain)
        while True:
            match_of_subdomains_of_desired_subdomain_or_domain = re.search(sub_reg,content[last_ending_index_of_subdomains_of_desired_subdomain_or_domain:])
            match_of_desired_domain = re.search(desired_domain,content[last_ending_index_of_desired_domain:])

            if match_of_desired_domain == None: 
                return False
            elif match_of_desired_domain != None and match_of_subdomains_of_desired_subdomain_or_domain == None:
                return True

            last_ending_index_of_subdomains_of_desired_subdomain_or_domain += match_of_subdomains_of_desired_subdomain_or_domain.end()
            last_ending_index_of_desired_domain += match_of_desired_domain.end()

            if last_ending_index_of_subdomains_of_desired_subdomain_or_domain != last_ending_index_of_desired_domain:
                return True

    # log_file = open("logfile.log", "a")
    # log_file.write(proxy + " here2" + "\n")
    # log_file.close()
    # try:
    def get_all_values(d):
        values = []

        def extract_values(obj):
            if isinstance(obj, dict):
                for value in obj.values():
                    extract_values(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_values(item)
            else:
                values.append(obj)

        extract_values(d)
        return "_".join(values)
    
    def filename_processor(line):

        # Replace 'LMAOPATH' with '/'
        line = line.replace('LMAOPATH', '/')

        # Remove double quotes
        line = line.replace('"', '')

        # Prefix the line with 'https://web.archive.org/web/'
        line = f"https://web.archive.org/web/{line.strip()}"

        # Fix 'https//' to 'https://'
        line = line.replace('https//', 'https://')

        # Fix 'http//' to 'http://'
        line = line.replace('http//', 'http://')

        # Adjust URLs to include port numbers correctly
        line = re.sub(r'(https?://[^/]*)(80|443)(/.*)', r'\1:\2\3', line)

        # Extract the part after the 5th '/' (index 6)
        final_line = "/".join(line.split("/")[5:])

        return final_line

    if os.path.exists(f'/home/deus/.config/waymore/results/{domain}'):
        downloaded_files_of_domain = os.listdir(f'/home/deus/.config/waymore/results/{domain}')
        if len(downloaded_files_of_domain) > 0:
            if "html_based_search" not in args.file_type:
                for interested_keyword in keywords_we_find_sources_for:
                    should_i_break_too = False
                    for file_name in downloaded_files_of_domain:
                        try:
                            # output = subprocess.run(f' bash -c \' grep -i -I "{interested_keyword}" /home/deus/.config/waymore/results/{domain}/{file} \'  ', stdin=subprocess.DEVNULL, shell=True, capture_output=True, text=True, timeout=60).stdout.lower()
                            with open(f"/home/deus/.config/waymore/results/{domain}/{file_name}", 'r') as file:
                                output = file.read()
                                if meticulous_check:
                                    if is_the_interested_domain_in_content(output, interested_keyword):
                                        if interested_keyword not in domains_and_their_sources.keys():
                                            domains_and_their_sources[interested_keyword] = manager.list()
                                        domains_and_their_sources[interested_keyword].append(domain)
                                        should_i_break_too = True
                                        break
                                else:
                                    if "_download" in args.file_type:
                                        if ',' in interested_keyword:
                                            multiple_keywords_exist_in_the_same_file = True
                                            for keyword in interested_keyword.split(","):
                                                if not re.search(re.escape(keyword), output, re.IGNORECASE):
                                                    multiple_keywords_exist_in_the_same_file = False
                                                    break
                                            if multiple_keywords_exist_in_the_same_file:
                                                if interested_keyword not in domains_and_their_sources.keys():
                                                    domains_and_their_sources[interested_keyword] = manager.list()

                                                if file_name not in domains_and_their_sources[interested_keyword] and (".yaml" in file_name or ".yml" in file_name or ".json" in file_name or ".js" in file_name):
                                                    domains_and_their_sources[interested_keyword].append(file_name)
                                                    with mv_lock:
                                                        os.rename(f"/home/deus/.config/waymore/results/{domain}", f"{wayback_dir}/{domain}")
                                                        size_in_bytes = get_directory_size(f"{wayback_dir}")
                                                        if size_in_bytes > 5 * 1024**3:
                                                            in_extraction = True
                                                            while True:
                                                                waymore_proc = subprocess.run(
                                                                    'ps aux | grep waymore',
                                                                    shell=True,
                                                                    stdout=subprocess.PIPE,
                                                                    stderr=subprocess.DEVNULL
                                                                )
                                                                if waymore_proc.returncode == 1:
                                                                    time.sleep(10)
                                                                    continue
                                                                
                                                                break

                                                            current_source = "/" + "/".join(wayback_dir.strip("/").split("/")[:len(wayback_dir.split('/')) - 2])
                                                            # current_source = os.path.join("/", wayback_dir.strip("/").split("/")[0])

                                                            files = os.listdir(f'{current_source}/')
                                                            tarballs_count = len([f for f in files if f.endswith('.tar.gz') or f.endswith('.tgz')])


                                                            subprocess.run(f"tar -czf {current_source}/archive_part_{tarballs_count}.tar.gz {wayback_dir} && rm -rf {wayback_dir} && mkdir {wayback_dir}", shell=True)

                                                            in_extraction = False
                                                            
                                                    should_i_break_too = True
                                                    break
                                        
                                        else:
                                            if re.search(re.escape(interested_keyword), output, re.IGNORECASE):
                                                if interested_keyword not in domains_and_their_sources.keys():
                                                    domains_and_their_sources[interested_keyword] = manager.list()

                                                if file_name not in domains_and_their_sources[interested_keyword] and (".yaml" in file_name or ".yml" in file_name or ".json" in file_name or ".js" in file_name):
                                                    domains_and_their_sources[interested_keyword].append(file_name)
                                                    with mv_lock:
                                                        os.rename(f"/home/deus/.config/waymore/results/{domain}", f"{wayback_dir}/{domain}")
                                                        size_in_bytes = get_directory_size(f"{wayback_dir}")
                                                        if size_in_bytes > 5 * 1024**3:
                                                            in_extraction = True
                                                            while True:
                                                                waymore_proc = subprocess.run(
                                                                    'ps aux | grep waymore',
                                                                    shell=True,
                                                                    stdout=subprocess.PIPE,
                                                                    stderr=subprocess.DEVNULL
                                                                )
                                                                if waymore_proc.returncode == 1:
                                                                    time.sleep(10)
                                                                    continue
                                                                    
                                                                break
                                                            
                                                            current_source = "/" + "/".join(wayback_dir.strip("/").split("/")[:len(wayback_dir.split('/')) - 2])
                                                            # return "/" + "/".join(parts[:3])
                                                            # current_source = os.path.join("/", wayback_dir.strip("/").split("/")[0])

                                                            files = os.listdir(f'{current_source}/')
                                                            tarballs_count = len([f for f in files if f.endswith('.tar.gz') or f.endswith('.tgz')])

                                                            subprocess.run(f"tar -czf {current_source}/archive_part_{tarballs_count}.tar.gz {wayback_dir} && rm -rf {wayback_dir} && mkdir {wayback_dir}", shell=True)

                                                            in_extraction = False
                                                            
                                                    should_i_break_too = True
                                                    break
                                    else:
                                        if re.search(re.escape(interested_keyword), output, re.IGNORECASE):
                                            if interested_keyword not in domains_and_their_sources.keys():
                                                domains_and_their_sources[interested_keyword] = manager.list()

                                            domains_and_their_sources[interested_keyword].append(domain)
                                            should_i_break_too = True
                                            break
                        except Exception as e:
                            log_file = open("logfile.log", "a")
                            log_file.write(f"An error occurred: {e} \n")
                            log_file.close()
                    if should_i_break_too:
                        break
            
            else:
                for file_name in downloaded_files_of_domain:
                    try:
                        with open(f"/home/deus/.config/waymore/results/{domain}/{file_name}", 'r') as file:
                            output = file.read()
                            forms_parsed = zetanize(output)
                            forms_value = get_all_values(forms_parsed)
                            with forms_urls_output_lock:
                                if forms_value not in forms:
                                    forms.append(forms_value)
                                    with open(f"./pages_with_forms_{pages_with_forms_count}.txt", "a") as pages_with_forms:
                                        pages_with_forms.write(f'{filename_processor(file_name)}' + "\n")
                                
                                if re.search(r'type="file"', output, re.IGNORECASE):
                                    with open(f"./pages_with_file_upload_{pages_with_forms_count}.txt", "a") as pages_with_forms:
                                        pages_with_forms.write(f'{filename_processor(file_name)}' + "\n")
                                        
                    except Exception as e:
                        log_file = open("logfile.log", "a")
                        log_file.write(f"An error occurred: {e} \n")
                        log_file.close()

    # except:
    #     pass

    # log_file = open("logfile.log", "a")
    # log_file.write(proxy + " here3" + "\n")
    # log_file.close()
    
    subprocess.run(f'rm -rf /home/deus/.config/waymore/results/{domain} ', shell=True, executable='/bin/bash')
    
    log_file = open("logfile.log", "a")
    log_file.write("Finished " + str(counter.value) + "/" + str(domains_len) + "\n")
    log_file.close()
    with counter.get_lock():
        counter.value += 1

subprocess.run(f'rm waymore_output_*.txt', shell=True, executable='/bin/bash')

pool = multiprocessing.Pool(len(proxies))
pool.map(source_identifier, domains, chunksize=1)

subprocess.run(f'rm -rf /home/deus/.config/waymore/results/* ', shell=True, executable='/bin/bash')

new_domains_and_their_sources = dict()
for key,value in domains_and_their_sources.items():
    new_domains_and_their_sources[key] = list(value)

sources_based_source_search_outputs_count = 0

for f_or_d in os.listdir('./'):
    if "sources_based_source_search_output" in f_or_d:
        sources_based_source_search_outputs_count += 1

sources_based_source_search_outputs_count += 1
with open(f'sources_based_source_search_output_{sources_based_source_search_outputs_count}.json','w') as file:
    file.write(json.dumps(new_domains_and_their_sources))


