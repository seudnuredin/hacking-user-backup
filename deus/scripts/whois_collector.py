import multiprocessing
try:
   multiprocessing.set_start_method('fork', force=True)
   print("forked")
except RuntimeError:
    print("unable to fork!")
    exit()

import os
import json
import ipaddress
import dns.resolver
import urllib3
import re
import time
import subprocess
import copy
import threading
import tldextract

tlds = {'zip', 'llc', 'memorial', 'cpa', 'barclays', 'dz', 'accountant', 'temasek', 'mattel', 'site', 'tt', 'solar', 'ricoh', 'km', 'kyoto', 'haus', 'baidu', 'jetzt', 'flickr', 'ally', 'management', 'xn--pssy2u', 'engineer', 'allstate', 'garden', 'xn--rhqv96g', 'forsale', 'organic', 'estate', 'rentals', 'surgery', 'gmo', 'mt', 'baseball', 'buzz', 'rugby', 'design', 'shangrila', 'delta', 'gt', 'food', 'restaurant', 'redumbrella', 'lundbeck', 'by', 'af', 'dk', 'barefoot', 'page', 'vegas', 'hyundai', 'pn', 'softbank', 'mr', 'review', 'gh', 'afl', 'jp', 'recipes', 'monash', 'airforce', 'ferrero', 'academy', 'hbo', 'tc', 'capital', 'xn--3bst00m', 'shaw', 'leclerc', 'sl', 'xn--42c2d9a', 'me', 'sn', 'voyage', 'citadel', 'ping', 'bi', 'erni', 'seek', 'yun', 'asda', 'shell', 'wiki', 'baby', 'dot', 'eu', 'fly', 'hospital', 'goodyear', 'anz', 'vanguard', 'insurance', 'kr', 'zw', 'tz', 'xn--otu796d', 'travelersinsurance', 'ai', 'photo', 'africa', 'loan', 'otsuka', 'tickets', 'gdn', 'vana', 'sd', 'ie', 'schaeffler', 'tn', 'legal', 'money', 'xn--xkc2dl3a5ee0h', 'iq', 'marshalls', 'voto', 'ae', 'cv', 'lexus', 'sex', 'sexy', 'jewelry', 'sew', 'quest', 'dclk', 'xn--6qq986b3xl', 'dvr', 'discount', 'hotmail', 'yachts', 'toshiba', 'barcelona', 'suzuki', 'hk', 'yokohama', 'email', 'gripe', 'hair', 'aeg', 'bike', 'man', 'skype', 'ing', 'city', 'aarp', 'accenture', 'abc', 'fi', 'cipriani', 'xn--flw351e', 'uz', 'ge', 'natura', 'xn--mgbca7dzdo', 'extraspace', 'events', 'read', 'sharp', 'amazon', 'forum', 'investments', 'beauty', 'prod', 'vn', 'gl', 'click', 'immobilien', 'vote', 'chase', 'netflix', 'smile', 'ss', 'abb', 'silk', 'tattoo', 'jot', 'horse', 'chrome', 'international', 'ifm', 'company', 'hyatt', 'amex', 'xn--j1amh', 'army', 'mma', 'ltd', 'hotels', 'homes', 'vacations', 'do', 'university', 'auto', 'kg', 'stockholm', 'claims', 'film', 'xn--j6w193g', 'wedding', 'versicherung', 'am', 'xn--5tzm5g', 'social', 'im', 'diet', 'tushu', 'eurovision', 'uk', 'george', 'book', 'hamburg', 'faith', 'xn--d1alf', 'theatre', 'open', 'sanofi', 'uno', 'dabur', 'audible', 'lawyer', 'pin', 'sbi', 'holiday', 'sucks', 'citic', 'xn--nyqy26a', 'xn--4dbrk0ce', 'bentley', 'xn--fiq228c5hs', 'physio', 'as', 'nc', 'tienda', 'nab', 'xn--9et52u', 'guru', 'bank', 'business', 'engineering', 'grainger', 'dish', 'diamonds', 'amfam', 'rehab', 'bbc', 'office', 'save', 'analytics', 'sener', 'free', 'xn--fzc2c9e2c', 'ms', 'la', 'delivery', 'kids', 'xn--kprw13d', 'sv', 'lease', 'jio', 'cyou', 'taxi', 'ax', 'itau', 'tiaa', 'ipiranga', 'xn--fiqz9s', 'xn--node', 'network', 'xn--90ais', 'lotto', 'es', 'webcam', 'pw', 'xxx', 'bm', 'xn--80asehdb', 'xn--tckwe', 'compare', 'safety', 'pramerica', 'blog', 'hitachi', 'fox', 'earth', 'center', 'yt', 'actor', 'makeup', 'desi', 'xn--45br5cyl', 'xn--vermgensberatung-pwb', 'luxe', 'pccw', 'best', 'cm', 'cz', 'ren', 'xn--tiq49xqyj', 'jobs', 'kim', 'vision', 'mit', 'jo', 'rip', 'music', 'secure', 'car', 'nissan', 'smart', 'nowruz', 'school', 'xn--ngbe9e0a', 'sh', 'maison', 'lifestyle', 'comcast', 'mls', 'ao', 'brother', 'nissay', 'bond', 'new', 'kz', 'bzh', 'domains', 'lighting', 'lego', 'boehringer', 'attorney', 'barclaycard', 'kred', 'java', 'fish', 'market', 'be', 'cool', 'jeep', 'kerryproperties', 'life', 'sling', 'yamaxun', 'tr', 'travel', 'lamer', 'cologne', 'tatamotors', 'kw', 'drive', 'dental', 'xn--3ds443g', 'flights', 'pioneer', 'hm', 'pf', 'sncf', 'pm', 'progressive', 'mango', 'racing', 'mc', 'cc', 'ky', 'finance', 'si', 'singles', 'axa', 'cooking', 'virgin', 'vlaanderen', 'lancaster', 'mp', 'cloud', 'sarl', 'cn', 'soy', 'productions', 'healthcare', 'xn--9krt00a', 'xn--gk3at1e', 'fido', 'arab', 'immo', 'bt', 'xn--11b4c3d', 'honda', 'scholarships', 'abogado', 'epson', 'xn--o3cw4h', 'aero', 'cd', 'co', 'family', 'ice', 'wolterskluwer', 'skin', 'aaa', 'xn--3e0b707e', 'sandvik', 'ruhr', 'rw', 'sony', 'pub', 'fit', 'coach', 'cars', 'plumbing', 'download', 'poker', 'amica', 'run', 'spa', 'buy', 'hr', 'salon', 'xn--1ck2e1b', 'farmers', 'dad', 'comsec', 'kp', 'monster', 'doctor', 'beats', 'aw', 'ac', 'xn--czru2d', 'grocery', 'med', 'alipay', 'guge', 'surf', 'airbus', 'tours', 'zara', 'xn--c1avg', 'ls', 'goldpoint', 'juniper', 'kuokgroup', 'realtor', 'xn--kcrx77d1x4a', 'aramco', 'fo', 'xn--qxa6a', 'xn--xhq521b', 'love', 'cleaning', 'xn--e1a4c', 'yahoo', 'juegos', 'nr', 'frogans', 'gratis', 'broadway', 'goo', 'xin', 'kh', 'land', 'xihuan', 'citi', 'nokia', 'like', 'dev', 'report', 'xn--h2breg3eve', 'mom', 'olayangroup', 'xn--q7ce6a', 'ad', 'stream', 'latrobe', 'dog', 'gallup', 'press', 'calvinklein', 'vu', 'mw', 'gold', 'cruises', 'athleta', 'commbank', 'gal', 'tube', 'play', 'sz', 'xn--54b7fta0cc', 'career', 'org', 'tax', 'app', 'koeln', 'lu', 'call', 'broker', 'net', 'photography', 'shoes', 'tci', 'boston', 'world', 'bio', 'weber', 'supplies', 'verisign', 'ye', 'rogers', 'dj', 'it', 'security', 'aetna', 'kn', 'energy', 'vi', 'joburg', 'xn--mgbai9azgqp6j', 'xn--gecrj9c', 'samsclub', 'intuit', 'moi', 'xn--pgbs0dh', 'bbva', 'space', 'sport', 'ht', 'media', 'bingo', 'news', 'flir', 'republican', 'accountants', 'stada', 'case', 'fidelity', 'bridgestone', 'fun', 'trading', 'bargains', 'xn--qxam', 'itv', 'realestate', 'zone', 'wien', 'nec', 'ollo', 'gap', 'ventures', 'xn--p1acf', 'emerck', 'date', 'to', 'np', 'dupont', 'ws', 'omega', 'wanggou', 'mg', 'diy', 'sa', 'ceo', 'mtn', 'na', 'kddi', 'xn--j1aef', 'mitsubishi', 'dell', 'author', 'samsung', 'homesense', 'gf', 'durban', 'help', 'ck', 'bar', 'nyc', 'church', 'trv', 'lotte', 'movie', 'tw', 'youtube', 'qa', 'win', 'xn--zfr164b', 'parts', 'men', 'ci', 'jm', 'xn--1qqw23a', 'miami', 'lat', 'americanexpress', 'pics', 'pohl', 'apple', 'furniture', 'tdk', 'windows', 'latino', 'statefarm', 'auspost', 'contact', 'democrat', 'nike', 'pars', 'select', 'schwarz', 'vip', 'consulting', 'voting', 'edeka', 'lipsy', 'stc', 'creditcard', 'je', 'williamhill', 'prime', 'courses', 'xn--ygbi2ammx', 'dunlop', 'wine', 'motorcycles', 'landrover', 'xn--s9brj9c', 'ro', 'credit', 'clinique', 'playstation', 'gi', 'xn--hxt814e', 'bz', 'deloitte', 'coupon', 'saxo', 'prof', 'bet', 'mo', 'praxi', 'lasalle', 'homedepot', 'al', 'map', 'edu', 'soccer', 'il', 'er', 'vg', 'xn--mgb9awbf', 'bible', 'paris', 'xn--imr513n', 'got', 'gucci', 'orange', 'archi', 'eat', 'netbank', 'ug', 'schmidt', 'nico', 'ag', 'construction', 'feedback', 'xn--cck2b3b', 'flowers', 'xn--mgberp4a5d4ar', 'frl', 'xn--cg4bki', 'bbt', 'xn--80aqecdr1a', 'mobile', 'avianca', 'bh', 'red', 'pl', 'xn--9dbq2a', 'channel', 'ftr', 'software', 'place', 'xn--mgbgu82a', 'xn--w4r85el8fhu5dnra', 'exposed', 'yandex', 'agakhan', 'bosch', 'globo', 'staples', 'capetown', 'beer', 'frontier', 'va', 'caravan', 'gov', 'uy', 'abudhabi', 'arpa', 'search', 'xn--c2br7g', 'tl', 'yodobashi', 'vet', 'mz', 'lacaixa', 'target', 'villas', 'rexroth', 'hkt', 'tools', 'asia', 'contractors', 'viking', 'xn--mgbc0a9azcg', 'pro', 'ril', 'art', 'coupons', 'kpmg', 'xn--vuq861b', 'dds', 'meme', 'jnj', 'nz', 'website', 'tirol', 'abbvie', 'condos', 'lplfinancial', 'sina', 'xn--czr694b', 'unicom', 'gq', 'americanfamily', 'careers', 'xn--wgbl6a', 'bestbuy', 'eg', 'xn--fpcrj9c3d', 'gmx', 'properties', 'cl', 'bharti', 'ubank', 'wtc', 'lk', 'mx', 'xn--lgbbat1ad8j', 'xn--3hcrj9c', 'corsica', 'rs', 'hu', 'bayern', 'adult', 'xn--h2brj9c', 'wtf', 'florist', 'codes', 'xn--mgbtx2b', 'xn--mgbah1a3hjkrd', 'shiksha', 'lol', 'theater', 'xn--czrs0t', 'nexus', 'xn--unup4y', 'viajes', 'gbiz', 'xn--45brj9c', 'limited', 'sbs', 'xn--gckr3f0f', 'bo', 'ch', 'ford', 'eus', 'ninja', 'hosting', 'education', 'town', 'bot', 'catholic', 'nfl', 'ski', 'scb', 'able', 'st', 'bom', 'rest', 'charity', 'au', 'how', 'ke', 'supply', 'xn--6frz82g', 'pnc', 'xn--mgbx4cd0ab', 'agency', 'xn--4gbrim', 'dating', 'xn--i1b6b1a6a2e', 'xn--jvr189m', 'ba', 'bb', 'ne', 'audi', 'xn--80aswg', 'glass', 'plus', 'kpn', 'xn--mgbpl2fh', 'xn--eckvdtc9d', 'ggee', 'vc', 'gy', 'ooo', 'xn--ngbrx', 'blockbuster', 'trade', 'toys', 'swiss', 'xn--mgbt3dhd', 'bnpparibas', 'toyota', 'digital', 'mini', 'kfh', 'xn--fjq720a', 'tkmaxx', 'xn--qcka1pmc', 'neustar', 'viva', 'apartments', 'aol', 'xn--io0a7i', 'visa', 'nrw', 'tel', 'ott', 'allfinanz', 'dhl', 'xfinity', 'phone', 'om', 'fishing', 'xn--8y0a063a', 'aig', 'data', 'cash', 'nba', 'enterprises', 'community', 'college', 'mn', 'br', 'hermes', 'locker', 'shop', 'game', 'works', 'booking', 'show', 'philips', 'ph', 'hiv', 'ads', 'cal', 'cfa', 'guide', 'lt', 'ua', 'meet', 'ngo', 'xn--5su34j936bgsg', 'bf', 'kindle', 'casa', 'xn--2scrj9c', 'xn--p1ai', 'tech', 'clothing', 'guardian', 'chat', 'xn--nqv7fs00ema', 'pa', 'istanbul', 'xn--55qx5d', 'associates', 'basketball', 'dentist', 'xn--g2xx48c', 'hot', 'xn--vhquv', 'xn--mix891f', 'woodside', 'canon', 'xbox', 'dealer', 'de', 'godaddy', 'xn--mgbi4ecexp', 'uol', 'xn--cckwcxetd', 'nextdirect', 'cw', 'fail', 'boats', 'style', 'thd', 'financial', 'cat', 'pwc', 'bostik', 'gift', 'xn--mgba3a4f16a', 'xn--vermgensberater-ctb', 'farm', 'cx', 'reisen', 'aq', 'partners', 'tips', 'cafe', 'moe', 'prudential', 'fairwinds', 'walter', 'luxury', 'bauhaus', 'crs', 'gd', 'gw', 'here', 'pharmacy', 'int', 'th', 'pt', 'za', 'oracle', 'loans', 'su', 'richardli', 'law', 'msd', 'shia', 'locus', 'protection', 'banamex', 'hdfcbank', 'tvs', 'foundation', 'taipei', 'rent', 'anquan', 'name', 'nowtv', 'rodeo', 'gu', 'ml', 'camp', 'quebec', 'host', 'ieee', 'ist', 'io', 'xn--mgbbh1a', 'circle', 'sb', 'sc', 'whoswho', 'gr', 'green', 'menu', 'gallery', 'fk', 'xn--rovu88b', 'hughes', 'berlin', 'gn', 'pet', 'akdn', 'discover', 'porn', 'fan', 'firmdale', 'mint', 'xn--l1acc', 'cards', 'ee', 'industries', 'chanel', 'sandvikcoromant', 've', 'cfd', 'olayan', 'catering', 'post', 'tatar', 'cy', 'md', 'sk', 'blue', 'google', 'storage', 'id', 'kerrylogistics', 'onl', 'eco', 'icu', 'tm', 'cr', 'moto', 'reise', 'airtel', 'politie', 'box', 'fans', 'ir', 'fujitsu', 'giving', 'pr', 'zero', 'cab', 'xn--fzys8d69uvgm', 'fyi', 'xn--45q11c', 'alstom', 'kitchen', 'se', 'ar', 'xn--xkc2al3hye2a', 'xyz', 'fage', 'store', 'video', 'ec', 'gp', 'observer', 'sale', 'day', 'kiwi', 'osaka', 'sj', 'xn--mxtq1m', 'nagoya', 'firestone', 'christmas', 'jcb', 'rsvp', 'my', 'xn--jlq480n2rg', 'institute', 'esq', 'mov', 'imamat', 'rocks', 'inc', 'obi', 'gay', 'tg', 'xn--ses554g', 'nf', 'sx', 'hiphop', 'krd', 'tennis', 'gifts', 'tunes', 'realty', 'goog', 'irish', 'mckinsey', 'xn--t60b56a', 'travelers', 'ca', 'cisco', 'limo', 're', 'docs', 'technology', 'audio', 'joy', 'team', 'mq', 'cf', 'xn--mgbaam7a8h', 'winners', 'xn--fhbei', 'xn--mgbbh1a71e', 'deal', 'is', 'sydney', 'xn--mgbcpq6gpa1a', 'mk', 'tjmaxx', 'jmp', 'sg', 'lilly', 'lc', 'li', 'jll', 'arte', 'xn--yfro4i67o', 'services', 'wf', 'creditunion', 'exchange', 'nra', 'mobi', 'ismaili', 'casino', 'cymru', 'xn--q9jyb4c', 'talk', 'support', 'mba', 'online', 'photos', 'rio', 'lb', 'sas', 'xn--fiq64b', 'work', 'song', 'pictet', 'xn--80ao21a', 'blackfriday', 'zuerich', 'pg', 'today', 'vig', 'guitars', 'helsinki', 'dnp', 'android', 'lr', 'com', 'tui', 'no', 'imdb', 'tab', 'walmart', 'xn--mgba7c0bbn0a', 'statebank', 'science', 'link', 'cg', 'fedex', 'wow', 'fitness', 'ly', 'group', 'us', 'ikano', 'dvag', 'volvo', 'gallo', 'srl', 'marriott', 'ntt', 'ki', 'xn--mgba3a3ejt', 'xn--55qw42g', 'merckmsd', 'club', 'hisamitsu', 'llp', 'amsterdam', 'trust', 'ga', 'systems', 'alibaba', 'xn--3pxu8k', 'xn--mgbayh7gpa', 'bid', 'jpmorgan', 'xn--kput3i', 'taobao', 'cruise', 'party', 'qpon', 'solutions', 'lifeinsurance', 'care', 'ng', 'crown', 'lamborghini', 'xn--h2brj9c8c', 'xn--ngbc5azd', 'py', 'hn', 'tk', 'panasonic', 'saarland', 'london', 'kerryhotels', 'teva', 'navy', 'gives', 'td', 'capitalone', 'house', 'vivo', 'gg', 'gmail', 'xn--mk1bu44c', 'chintai', 'rich', 'ubs', 'mm', 'futbol', 'mv', 'nl', 'xerox', 'bcg', 'markets', 'xn--90ae', 'studio', 'hdfc', 'gs', 'games', 'wed', 'aco', 'so', 'safe', 'sr', 'aws', 'vin', 'hsbc', 'ma', 'norton', 'biz', 'gent', 'tf', 'insure', 'cern', 'gb', 'top', 'living', 'homegoods', 'pictures', 'bofa', 'fresenius', 'lidl', 'directory', 'degree', 'pink', 'lpl', 'mu', 'xn--wgbh1c', 'fj', 'dance', 'training', 'football', 'mtr', 'okinawa', 'band', 'ni', 'mil', 'reliance', 'nhk', 'bms', 'pru', 'pk', 'infiniti', 'seven', 'hangout', 'xn--w4rs40l', 'bloomberg', 'ru', 'cheap', 'ibm', 'zm', 'xn--rvc1e0am3e', 'watches', 'in', 'bw', 'golf', 'auction', 'gop', 'gm', 'now', 'cbre', 'microsoft', 'weatherchannel', 'forex', 'azure', 'pe', 'ericsson', 'xn--b4w605ferd', 'museum', 'study', 'et', 'bv', 'graphics', 'mormon', 'sfr', 'weather', 'madrid', 'ltda', 'nu', 'brussels', 'moscow', 'dm', 'bs', 'tmall', 'vodka', 'clubmed', 'global', 'lefrak', 'tj', 'gea', 'marketing', 'you', 'ryukyu', 'dtv', 'cbn', 'health', 'xn--fiqs8s', 'hockey', 'moda', 'bmw', 'sohu', 'origins', 'stcgroup', 'deals', 'cam', 'bd', 'mlb', 'computer', 'lincoln', 'datsun', 'shopping', 'cu', 'gle', 'equipment', 'scot', 'xn--d1acj3b', 'swatch', 'zappos', 'xn--90a3ac', 'xn--ogbpf8fl', 'fm', 'wales', 'az', 'mortgage', 'xn--fct429k', 'black', 'bradesco', 'clinic', 'tires', 'radio', 'weibo', 'next', 'fr', 'room', 'fire', 'genting', 'coop', 'xn--clchc0ea0b2g2a9gcd', 'expert', 'tv', 'pid', 'tjx', 'direct', 'melbourne', 'watch', 'build', 'sky', 'one', 'foo', 'jaguar', 'redstone', 'sap', 'nikon', 'yoga', 'abbott', 'cba', 'xn--efvy88h', 'ps', 'at', 'ferrari', 'promo', 'bg', 'reit', 'kaufen', 'lgbt', 'dubai', 'sy', 'xn--nqv7f', 'tokyo', 'jprs', 'lanxess', 'phd', 'fund', 'live', 'ovh', 'sm', 'camera', 'lds', 'xn--y9a3aq', 'seat', 'fast', 'bj', 'ink', 'aquarelle', 'schule', 'boutique', 'mh', 'wme', 'coffee', 'country', 'toray', 'xn--80adxhks', 'gmbh', 'spot', 'cricket', 'wang', 'sakura', 'xn--kpry57d', 'xn--mgbab2bd', 'shouji', 'komatsu', 'info', 'bn', 'boo', 'alsace', 'xn--30rr7y', 'pay', 'property', 'total', 'autos', 'ups', 'bing', 'pfizer', 'express', 'pizza', 'cuisinella', 'fashion', 'weir', 'maif', 'repair', 'reviews', 'bcn', 'holdings', 'xn--bck1b9a5dre4c', 'rwe', 'final', 'ong', 'builders', 'kosher', 'star', 'kia', 'lv', 'icbc'}

tlds = list(tlds)
tlds.sort(reverse=True, key=len)


# proxies = ["self"]
# with open('/home/deus/documents/proxies.txt') as proxy_file:
#     for proxy in proxy_file:
#         proxy = proxy.replace("\n","")
#         if proxy != "":
#             proxy = proxy.split(':')
#             proxies.append(f"{proxy[0]}:{proxy[1]}")

# manager = multiprocessing.Manager()
# used_proxies_across_processes = manager.list()

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
    extracted = tldextract.extract(subdomain)
    base_domain = f"{extracted.domain}.{extracted.suffix}"
    return base_domain


def asset_list_prepare():
    assets = set()

    with open('assets_of_target_and_its_acquisitions') as file:
        for asset in file:
            asset = asset.replace("\n","")
            if asset != "":
                assets.add(asset)
    with open('reverse_whois_output') as file:
        for asset in file:
            asset = asset.replace("\n","")
            if asset != "":
                assets.add(asset)
    with open('IP_based_reverse_dns_output') as file:
        for asset in file:
            asset = asset.replace("\n","")
            if asset != "":
                assets.add(asset)
    with open('ssl_certificate_grabbing_output') as file:
        for asset in file:
            asset = asset.replace("\n","")
            if asset != "":
                assets.add(asset)
    with open('tld_enum_output') as file:
        for asset in file:
            asset = asset.replace("\n","")
            if asset != "":
                assets.add(asset)

    return assets

def valid_ip(address):
    try:
        ipaddress.ip_address(address)
        return True
    except:
        return False

personal_whois_dict = dict()
# def target_personal_whois_info_manager():
# pattern = "^((?!-))(xn--)?[a-z0-9][a-z0-9-_]{0,61}[a-z0-9]{0,1}\.(xn--)?([a-z0-9\-]{1,61}|[a-z0-9-]{1,30}\.[a-z]{2,})$"
def recursively_finder(value):
    for name,value in value.items():
        # if "registrant" in name.lower() or "org" in name.lower() or "email" in name.lower() or "server" in name.lower():
        if "mail" in name.lower():
            recursively_adder(value, "email")
        elif "registrant org" in name.lower() or "registrant name" in name.lower():
            recursively_adder(value, "org")
        elif type(value) is dict:
            recursively_finder(value)
        # elif ("phone" in name.lower() or "fax" in name.lower()) and ("registrant phone ext" not in name.lower() and "registrant fax ext" not in name.lower()):
        #     recursively_adder(value, "phone")
        # elif "street" in name.lower():
        #     recursively_adder(value, "street")
def recursively_adder(u_value, field = "not desired field"):
    if type(u_value) is list:
        for i in u_value:
            if type(i) is not list and type(i) is not dict:
                if field not in personal_whois_dict.keys():
                    personal_whois_dict[field] = set()
                if len(i) > 3 and not ('@' not in i and valid_domain(i)):
                    personal_whois_dict[field].add(i)
            else:
                recursively_adder(i, field)
    elif type(u_value) is dict:
        for i in u_value.values():
            if type(i) is not list and type(i) is not dict:
                if field not in personal_whois_dict.keys():
                    personal_whois_dict[field] = set()
                if len(i) > 3 and not ('@' not in i and valid_domain(i)):
                    personal_whois_dict[field].add(i)
            else:
                recursively_adder(i, field)
    else:
        if field not in personal_whois_dict.keys():
            personal_whois_dict[field] = set()
        if len(u_value) > 3 and not ('@' not in u_value and valid_domain(u_value)):
            personal_whois_dict[field].add(u_value)
personal_whois_list = list()
assets = asset_list_prepare()
ips = set()
domains = set()
cnames = set()
def domains_list_generate(assets):
    with open('domains_to_be_used','w') as file:
        for asset in assets:
            if valid_domain(asset):
                file.write(asset + "\n")
            elif valid_subdomain(asset):
                file.write(get_domain_from_subdomain(asset) + "\n")
def recursively_cname_resolver(domain):
    subprocess.run(f' bash -c \' massdns <( echo {domain} ) -t A -q -r /home/deus/documents/resolvers-trusted.txt --retry REFUSED --retry FORMERR --retry SERVFAIL -i 10000 -s 500 -o S > ips_of_resolved_domains.txt \' ', shell=True, capture_output=True, text=True)
    try:
        records_response = subprocess.run(f"bash -c 'cat ./ips_of_resolved_domains.txt | cut -d \" \" -f3'", shell=True, capture_output=True, text=True).stdout.split("\n")
        for record in set(records_response):
            if not valid_ip(record) and record not in cnames and record != '':
                cnames.add(record)
                recursively_cname_resolver(record)
            elif valid_ip(record):
                ips.add(record)
    except:
        pass
def recursively_resolver():
    subprocess.run(f' bash -c \' massdns domains_to_be_used -t A -q -r /home/deus/documents/resolvers-trusted.txt --retry REFUSED --retry FORMERR --retry SERVFAIL -i 10000 -s 500 -o S > ips_of_resolved_domains.txt \' ', shell=True, capture_output=True, text=True)
    try:
        records_response = subprocess.run(f"bash -c 'cat ./ips_of_resolved_domains.txt | cut -d \" \" -f3'", shell=True, capture_output=True, text=True).stdout.split("\n")
        for record in set(records_response):
            if not valid_ip(record) and record not in cnames and record != '':
                cnames.add(record)
                recursively_cname_resolver(record)
            elif valid_ip(record):
                ips.add(record)
    except:
        pass
domains_list_generate(assets)
recursively_resolver()
for asset in assets:
    if valid_domain(asset):
        domains.add(asset)
    elif valid_subdomain(asset):
        domains.add(get_domain_from_subdomain(asset))
    elif "/" in asset:
        for ip in ipaddress.ip_network(asset):
            ips.add(ip)
    elif valid_ip(asset):
        ips.add(asset)
    else:
        print(f'{asset} asset that isn\'t domain, cidr, and ip found!')
ips = list(ips)
domains = list(domains)

def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

proxies = ["self"]
with open('/home/deus/documents/proxies.txt') as proxy_file:
    for proxy in proxy_file:
        proxy = proxy.replace("\n","")
        if proxy != "":
            proxy = proxy.split(':')
            proxies.append(f"{proxy[0]}:{proxy[1]}")

manager = multiprocessing.Manager()
used_proxies_across_processes = manager.list()
whois_list = manager.list()
domains_and_ips = list()
def domain_and_ips_whois(domain_or_ip):
    # global used_proxies_across_processes
    # global proxies
    global whois_list
    # exhausted_available_proxies = True
    # just in superstitious case to not miss out value of argument
    # while len(proxies) == len(used_proxies_across_processes):
    #     time.sleep(2)
    # proxy = list(set(proxies) - set(used_proxies_across_processes))[0]
    # used_proxies_across_processes.append(proxy)
    failure_count = 0
    while True:
        # if proxy == "self":
        whois_output = ""
        try:
            whois_output = json.loads(subprocess.run(f'jswhois {domain_or_ip}', shell=True, capture_output=True, text=True, timeout=90).stdout)
        except:
            pass
        # else:
        #     whois_output = json.loads(subprocess.run(f'mgraftcp --socks5 "{proxy}" --socks5_username "seudxs" --socks5_password "Nz7ZC7jZY54YfmG6Fc8a" jswhois {domain_or_ip}', shell=True, capture_output=True, text=True).stdout)
        
        if "Unable to connect" not in whois_output and whois_output != "":
            whois_list.append(whois_output)
            # error_count_file = open("logfile.log", "a")
            # error_count_file.write(str(whois_output) + "\n")
            # error_count_file.close()
            # used_proxies_across_processes.remove(proxy)
            break
        
        failure_count += 1
        error_count_file = open("error_count", "a")
        error_count_file.write(str(failure_count) + "\n")
        error_count_file.close()
        if failure_count > 3:
            break

domains_and_ips.extend(domains)
domains_and_ips.extend(ips)
pool = multiprocessing.Pool(50)
pool.map(domain_and_ips_whois, domains_and_ips, chunksize=1)
# pool.map(domain_and_ips_whois, domains_and_ips, chunksize=1)

for whois in whois_list:
    for i in whois:
        if type(i) is dict:
            recursively_finder(i)

def compare_strings(s):
    return s[::-1]

for name in personal_whois_dict.keys():
    part_of_personal_whois_list = list(personal_whois_dict[name])
    if name == "email":
        part_of_personal_whois_list = sorted(part_of_personal_whois_list, key=compare_strings)
    else:
        part_of_personal_whois_list.sort()
    for v in part_of_personal_whois_list:
        personal_whois_list.append(v)
personal_whois_list = list(dict.fromkeys(personal_whois_list))
# personal_whois_list = list(personal_whois_list)
# deletion processes
common_whois_chunks_to_be_ignored = open('/home/deus/targets/common_registrant_info_to_be_ignored','r+')
whois_chunks_to_be_ignored = open("registrant_info_to_be_ignored", "r+")
# automatic deletion
for whois_chunk in common_whois_chunks_to_be_ignored:
    whois_chunk = whois_chunk.replace("\n","")
    if whois_chunk in personal_whois_list:
        personal_whois_list.remove(whois_chunk)

personal_whois_list_new = copy.deepcopy(personal_whois_list)
for whois_chunk in whois_chunks_to_be_ignored:
    whois_chunk = whois_chunk.replace("\n","")
    for i in range(0, len(personal_whois_list)):
        if whois_chunk in personal_whois_list[i] and personal_whois_list[i] in personal_whois_list_new:
            personal_whois_list_new.remove(personal_whois_list[i])
personal_whois_list = personal_whois_list_new

common_whois_chunks_to_be_ignored.close()
whois_chunks_to_be_ignored.close()
personal_whois_list_new = list()
for i in range(0, len(personal_whois_list)):
    whois_chunk = personal_whois_list[i]
    if not valid_ip(whois_chunk) and not ("http" in whois_chunk) and not ("https" in whois_chunk):
        personal_whois_list_new.append(whois_chunk)
personal_whois_list = personal_whois_list_new
# save to a file

def exit_after_proper_save(file_name):
    assets = list()
    with open(file_name) as file:
        for asset in file:
            asset = asset.replace("\n","")
            if asset not in assets:
                assets.append(asset)
    with open(file_name,'w') as file:
        for asset in assets:
            file.write(asset + "\n")

with open('registrant_info_to_be_used','a') as file:
    for whois_chunk in personal_whois_list:
        file.write(whois_chunk + "\n")

exit_after_proper_save('registrant_info_to_be_used')

# target_personal_whois_info_manager()