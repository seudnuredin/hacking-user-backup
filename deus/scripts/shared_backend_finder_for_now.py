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
import time
import os
import shutil
import requests
import hashlib
import json
import socks
from botasaurus import *
import signal

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
    for asset in assets:
        if valid_domain(asset):
            domains.add(asset)
        elif valid_subdomain(asset):
            domains.add(get_domain_from_subdomain(asset))
    
    return list(domains)

proxies = ["self"]
for f_or_d in os.listdir('/home/deus/documents'):
    if "proxychains" in f_or_d:
        proxies.append(f_or_d)

# proxies_to_bypass_wafs = []
# port = 8080
# with open('/home/deus/documents/proxies.txt') as proxy_file:
#     for proxy in proxy_file:
#         proxy = proxy.replace("\n","")
#         if proxy != "":
#             proxy = proxy.split(':')
#             proxies_to_bypass_wafs.append(port)
#             subprocess.Popen(f'/bin/bash -c \' proxify -http-addr 127.0.0.1:{port} -socks5-proxy {proxy[0]}:{proxy[1]} /home/deus/downloads/httpRelay/relay -listen 127.0.0.1:{port} -socks {proxy[0]}:{proxy[1]} -socks-user seudxs -socks-pass Nz7ZC7jZY54YfmG6Fc8a  \' ', shell=True)
#             port += 1


manager = multiprocessing.Manager()
used_proxies_across_processes = manager.list()
domains_and_or_subdomains_with_their_shared_backends = manager.dict()
counter = multiprocessing.Value('i',1)
# source_counter_output = manager.dict()

domains_and_or_subdomains_we_should_find_shared_backends_for = list()
collected_domains = set()
domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains = dict()
domains_and_subdomains_we_should_look_for_shared_backends = set()

for i in range(1, len(sys.argv)):
    if "*" in sys.argv[i]:
        sys.argv[i] = sys.argv[i].replace("*.","")
        with open('domains.txt') as file:
            for domain in file:
                domain = domain.replace("\n","")
                if sys.argv[i] in domain:
                    domains_and_or_subdomains_we_should_find_shared_backends_for.append(domain)
    else:
        domains_and_or_subdomains_we_should_find_shared_backends_for.append(sys.argv[i])

subprocess.run(" bash -c \'  httpx -ports 80,443 -l domains.txt -timeout 10 -threads 50 -silent -o domains_with_web_servers_listening_on_common_ports \' ", shell=True)

with open('domains_with_web_servers_listening_on_common_ports') as file:
    for domain in file:
        domain = domain.replace("\n","")
        domain = domain.replace("http://","")
        domain = domain.replace("https://","")
        domain = domain.replace(":80","")
        domain = domain.replace(":443","")
        collected_domains.add(domain)

# domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains = list(domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains)

# domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains_len = len(domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains)

# with open('domains.txt') as file:
#     for domain in file:
#         domain = domain.replace("\n","")
#         collected_domains.add(domain)

# for domain in domain_list_prepare():
#     collected_domains.add(domain)
domains_and_or_subdomains_we_should_find_shared_backends_for_new = list()
for domain_or_subdomain_we_should_find_shared_backends_for in domains_and_or_subdomains_we_should_find_shared_backends_for:
    preserved_domain_or_subdomain_we_should_find_shared_backends_for = domain_or_subdomain_we_should_find_shared_backends_for

    domain_or_subdomain_we_should_find_shared_backends_for = domain_or_subdomain_we_should_find_shared_backends_for.split(".")
    for tld in tlds:
        if tld in domain_or_subdomain_we_should_find_shared_backends_for:
            domain_or_subdomain_we_should_find_shared_backends_for.remove(tld)
    
    # if len(domain_or_subdomain_we_should_find_shared_backends_for) > 0:
    #     domain_or_subdomain_we_should_find_shared_backends_for.pop()

    for i in range(0,len(domain_or_subdomain_we_should_find_shared_backends_for)):
        pattern = r'[0-9]'
        domain_or_subdomain_we_should_find_shared_backends_for[i] = re.sub(pattern, '', domain_or_subdomain_we_should_find_shared_backends_for[i])

    for collected_domain in collected_domains:
        preserved_collected_domain = collected_domain

        collected_domain = collected_domain.split(".")
        for tld in tlds:
            if tld in collected_domain:
                collected_domain.remove(tld)
        
        # if len(collected_domain) > 0:
        #     collected_domain.pop()

        for i in range(0,len(collected_domain)):
            pattern = r'[0-9]'
            collected_domain[i] = re.sub(pattern, '', collected_domain[i])
        
        if set(domain_or_subdomain_we_should_find_shared_backends_for).intersection(set(collected_domain)):
            if preserved_domain_or_subdomain_we_should_find_shared_backends_for not in domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains.keys():
                domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains[preserved_domain_or_subdomain_we_should_find_shared_backends_for] = list()
            domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains[preserved_domain_or_subdomain_we_should_find_shared_backends_for].append(preserved_collected_domain)
            domains_and_or_subdomains_we_should_find_shared_backends_for_new.append(preserved_collected_domain)
            # domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains.add(collected_domain)
    
domains_and_or_subdomains_we_should_find_shared_backends_for.extend(domains_and_or_subdomains_we_should_find_shared_backends_for_new)

# log_file = open("logfile.log", "a")
# log_file.write(str(domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains) + "\n")
# log_file.close()

# with open('domains_with_web_servers') as file:
#     for domain in file:
#         domain = domain.replace("\n","")
#         domain = domain.replace("http://","")
#         domain = domain.replace("https://","")
#         domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains.add(domain)

def download_links(domain):
    global proxies
    global used_proxies_across_processes
    global domains_and_or_subdomains_we_should_find_shared_backends_for
    
    while True:
        try:
            proxy = list(set(proxies) - set(used_proxies_across_processes))[0]
            used_proxies_across_processes.append(proxy)
            break
        except:
            time.sleep(2)

    failure_count = 0
    index_of_domain = domains_and_or_subdomains_we_should_find_shared_backends_for.index(domain)
    timeout_count = 0
    while True:
        if proxy == "self":
            try:
                subprocess.run(f' bash -c \' waymore -i {domain} -mode U -r 2 -xvt -xus -xav -xcc --no-subs -c /home/deus/.config/waymore/static_resources_config.yml &>> waymore_output_{index_of_domain}.txt \' ', shell=True, capture_output=True, text=True, timeout=1000)
            except subprocess.TimeoutExpired:
                timeout_count += 1
        else:
            try:
                subprocess.run(f' bash -c \' proxychains4 -f /home/deus/documents/{proxy} -q waymore -i {domain} -mode U -r 2 -xvt -xus -xav -xcc --no-subs -c /home/deus/.config/waymore/static_resources_config.yml &>> waymore_output_{index_of_domain}.txt  \' ', shell=True, capture_output=True, text=True, timeout=1000)
            except subprocess.TimeoutExpired:
                timeout_count += 1
        
        condition_of_waymore_output = subprocess.run(f'/bin/bash -c \'cat waymore_output_{index_of_domain}.txt \' ', shell=True, capture_output=True, text=True).stdout
        if "Links found on Wayback Machine" in condition_of_waymore_output or timeout_count == 2:
            used_proxies_across_processes.remove(proxy)
            break
        failure_count += 1
        error_count = open("error_count", "a")
        error_count.write(proxy + " " + domain + " "  + str(failure_count) + "\n")
        error_count.close()
        if failure_count > 5:
            used_proxies_across_processes.remove(proxy)
            break
    
    subprocess.run(f'/bin/bash -c \'rm waymore_output_{index_of_domain}.txt \' ', shell=True)
    
    # try:
    #     if os.path.exists(f"/home/deus/.config/waymore/results/{domain}/waymore.txt"):
    #         urls = subprocess.run(f' bash -c \' cat /home/deus/.config/waymore/results/{domain}/waymore.txt | uro \'  ', shell=True, capture_output=True, text=True, timeout=300).stdout.split("\n")
    #         urls_len = len(urls)
    #     else:
    #         urls_len = 0
    # except:
    #     pass

    # if urls_len > 0:
    # source_counter_output[domain] = urls_len

    # subprocess.run(f'/bin/bash -c \'rm -rf /home/deus/.config/waymore/results/{domain} \' ', shell=True)
    

subprocess.run(f'/bin/bash -c \'rm waymore_output_*.txt \' ', shell=True)

pool = multiprocessing.Pool(len(proxies))
pool.map(download_links, domains_and_or_subdomains_we_should_find_shared_backends_for, chunksize=1)


def find_shared_backends(domain_or_subdomain):
    global domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains_len
    global counter
    global domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains
    global domains_and_subdomains_we_should_look_for_shared_backends
    global domains_and_or_subdomains_with_their_shared_backends
    global manager
    # global proxies_to_bypass_wafs
    # global used_proxies_across_processes

    
    # while True:
    #     try:
    #         proxy = list(set(proxies_to_bypass_wafs) - set(used_proxies_across_processes))[0]
    #         proxy = f"http://127.0.0.1:{proxy}"
    #         used_proxies_across_processes.append(proxy)
    #         break
    #     except:
    #         time.sleep(2)

    index_of_domain_or_subdomain = domains_and_subdomains_we_should_look_for_shared_backends.index(domain_or_subdomain)
    
    def hash_file(filename):
        """"This function returns the SHA-1 hash
        of the file passed into it"""
        
        # make a hash object
        h = hashlib.sha1()
        
        # open file for reading in binary mode
        with open(filename,'rb') as file:
        
            # loop till the end of the file
            chunk = 0
            while chunk != b'':
                # read only 1024 bytes at a time
                chunk = file.read(1024)
                h.update(chunk)
        
        # return the hex representation of digest
        return h.hexdigest()
    
    @request(use_stealth=True)
    def return_hash_of_downloaded_file(request: AntiDetectRequests, data):
        hash_of_file = 0
        try:
            response = request.get(data, timeout=30)

            def save_it_as_file_get_its_sha1sum():
                hash_of_file = 0
                with open(f'web_resource_to_be_hashed_{index_of_domain_or_subdomain}', 'wb') as out_file:
                    out_file.write(response.content)
                hash_of_file = hash_file(f'web_resource_to_be_hashed_{index_of_domain_or_subdomain}')
                return hash_of_file
            
            try:
                if "content-type" in str(response.headers):
                    if "text/html" not in response.headers["content-type"]:
                        hash_of_file = save_it_as_file_get_its_sha1sum()
                    else:
                        if "cloudfront" in response.text.lower() or "cloudflare" in response.text.lower():
                            log_file = open("logfile.log", "a")
                            log_file.write("ip block detected at " + str(data) + "\n")
                            log_file.close()
                elif "Content-Type" in str(response.headers):
                    if "text/html" not in response.headers["Content-Type"]:
                        hash_of_file = save_it_as_file_get_its_sha1sum()
                    else:
                        if "cloudfront" in response.text.lower() or "cloudflare" in response.text.lower():
                            log_file = open("logfile.log", "a")
                            log_file.write("ip block detected" + str(data) + "\n")
                            log_file.close()
                else:
                    hash_of_file = save_it_as_file_get_its_sha1sum()
            except:
                hash_of_file = save_it_as_file_get_its_sha1sum()
        except:
            pass
        return hash_of_file

    for interested_domain_or_subdomain, potentially_similar_backends in domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains.items():
        if domain_or_subdomain in potentially_similar_backends:
            check_alternative_urls = True
            if os.path.exists(f"/home/deus/.config/waymore/results/{interested_domain_or_subdomain}/waymore.txt"):
                urls = subprocess.run(f' bash -c \' cat /home/deus/.config/waymore/results/{interested_domain_or_subdomain}/waymore.txt \'  ', shell=True, capture_output=True, text=True, timeout=300).stdout.split("\n")
                if len(urls) > 5:
                    check_alternative_urls = False
                unmatched_count = 0
                for url in urls:
                    if url == "":
                        continue
                    error_count = 0
                    file1_downloaded_successfully = False
                    
                    start_time = time.time()
                    hash_of_downloaded_of_interested_domain_url = return_hash_of_downloaded_file(data=url)
                    if hash_of_downloaded_of_interested_domain_url != 0:
                        file1_downloaded_successfully = True
                    elif (time.time() - start_time) > 60:
                        break
                    
                    file2_downloaded_successfully = False
                    
                    url_modified = url.replace(interested_domain_or_subdomain,domain_or_subdomain)

                    start_time = time.time()

                    hash_of_downloaded_of_domain_or_subdomain_url = return_hash_of_downloaded_file(data=url_modified)
                    if hash_of_downloaded_of_domain_or_subdomain_url != 0:
                        file2_downloaded_successfully = True
                    elif (time.time() - start_time) > 60:
                        break
                    
                    if file1_downloaded_successfully and file2_downloaded_successfully:
                        if hash_of_downloaded_of_interested_domain_url == hash_of_downloaded_of_domain_or_subdomain_url:
                            if interested_domain_or_subdomain not in domains_and_or_subdomains_with_their_shared_backends.keys():
                                domains_and_or_subdomains_with_their_shared_backends[interested_domain_or_subdomain] = manager.list()
                            domains_and_or_subdomains_with_their_shared_backends[interested_domain_or_subdomain].append(domain_or_subdomain)
                            log_file = open("logfile.log", "a")
                            log_file.write("found " + str(url_modified) + " " + str(url) + "\n")
                            log_file.close()
                            break
                        else:
                            unmatched_count += 1
                    elif file1_downloaded_successfully:
                        unmatched_count += 1
                    
                    if unmatched_count > 10:
                        break
            if check_alternative_urls:
                url = f"http://{interested_domain_or_subdomain}"
                error_count = 0
                file1_downloaded_successfully = False
                
                # start_time = time.time()
                hash_of_downloaded_of_interested_domain_url = return_hash_of_downloaded_file(data=url)
                if hash_of_downloaded_of_interested_domain_url != 0:
                    file1_downloaded_successfully = True
                # elif (time.time() - start_time) > 60:
                #     break
                
                file2_downloaded_successfully = False
                
                url_modified = url.replace(interested_domain_or_subdomain,domain_or_subdomain)
                # start_time = time.time()
                hash_of_downloaded_of_domain_or_subdomain_url = return_hash_of_downloaded_file(data=url_modified)
                if hash_of_downloaded_of_domain_or_subdomain_url != 0:
                    file2_downloaded_successfully = True
                # elif (time.time() - start_time) > 60:
                #     break
                
                if file1_downloaded_successfully and file2_downloaded_successfully:
                    if hash_of_downloaded_of_interested_domain_url == hash_of_downloaded_of_domain_or_subdomain_url:
                        if interested_domain_or_subdomain not in domains_and_or_subdomains_with_their_shared_backends.keys():
                            domains_and_or_subdomains_with_their_shared_backends[interested_domain_or_subdomain] = manager.list()
                        domains_and_or_subdomains_with_their_shared_backends[interested_domain_or_subdomain].append(domain_or_subdomain)
                        log_file = open("logfile.log", "a")
                        log_file.write("found " + str(url_modified) + " " + str(url) + "\n")
                        log_file.close()
                        break
                    # else:
                        # unmatched_count += 1
                # elif file1_downloaded_successfully:
                    # unmatched_count += 1
                
                # if unmatched_count > 20:
                    # break

            if os.path.exists(f"/home/deus/.config/waymore/results/{domain_or_subdomain}/waymore.txt") and check_alternative_urls:
                urls = subprocess.run(f' bash -c \' cat /home/deus/.config/waymore/results/{domain_or_subdomain}/waymore.txt \'  ', shell=True, capture_output=True, text=True, timeout=300).stdout.split("\n")
                unmatched_count = 0
                for url in urls:
                    if url == "":
                        continue
                    error_count = 0
                    file1_downloaded_successfully = False
                    
                    start_time = time.time()
                    hash_of_downloaded_of_interested_domain_url = return_hash_of_downloaded_file(data=url)
                    if hash_of_downloaded_of_interested_domain_url != 0:
                        file1_downloaded_successfully = True
                    elif (time.time() - start_time) > 60:
                        break
                    
                    file2_downloaded_successfully = False
                    
                    url_modified = url.replace(domain_or_subdomain,interested_domain_or_subdomain)

                    start_time = time.time()

                    hash_of_downloaded_of_domain_or_subdomain_url = return_hash_of_downloaded_file(data=url_modified)
                    if hash_of_downloaded_of_domain_or_subdomain_url != 0:
                        file2_downloaded_successfully = True
                    elif (time.time() - start_time) > 60:
                        break
                    
                    if file1_downloaded_successfully and file2_downloaded_successfully:
                        if hash_of_downloaded_of_interested_domain_url == hash_of_downloaded_of_domain_or_subdomain_url:
                            if interested_domain_or_subdomain not in domains_and_or_subdomains_with_their_shared_backends.keys():
                                domains_and_or_subdomains_with_their_shared_backends[interested_domain_or_subdomain] = manager.list()
                            domains_and_or_subdomains_with_their_shared_backends[interested_domain_or_subdomain].append(domain_or_subdomain)
                            log_file = open("logfile.log", "a")
                            log_file.write("found " + str(url_modified) + " " + str(url) + "\n")
                            log_file.close()
                            break
                        else:
                            unmatched_count += 1
                    elif file1_downloaded_successfully:
                        unmatched_count += 1
                    
                    if unmatched_count > 10:
                        break
    # used_proxies_across_processes.remove(proxy)
    log_file = open("logfile.log", "a")
    log_file.write("Finished " + str(counter.value) + "/" + str(domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains_len) + "\n")
    log_file.close()
    with counter.get_lock():
        counter.value += 1


for domains_and_subdomains_we_should_look_for_shared_backends_domain_or_subdomain in domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains.values():
    for domain_or_subdomain in domains_and_subdomains_we_should_look_for_shared_backends_domain_or_subdomain:
        domains_and_subdomains_we_should_look_for_shared_backends.add(domain_or_subdomain)

domains_and_subdomains_we_should_look_for_shared_backends = list(domains_and_subdomains_we_should_look_for_shared_backends)

domains_and_subdomains_we_should_look_for_shared_backends_domains_or_subdomains_len = len(domains_and_subdomains_we_should_look_for_shared_backends)

pool = multiprocessing.Pool(5)
pool.map(find_shared_backends, domains_and_subdomains_we_should_look_for_shared_backends, chunksize=1)

new_domains_and_or_subdomains_with_their_shared_backends = dict()
for key,value in domains_and_or_subdomains_with_their_shared_backends.items():
    new_domains_and_or_subdomains_with_their_shared_backends[key] = list(value)

with open(f'shared_backend_output.json','w') as file:
    file.write(json.dumps(new_domains_and_or_subdomains_with_their_shared_backends))

for domains_and_or_subdomains_with_their_shared_backends in domains_and_or_subdomains_we_should_find_shared_backends_for:
    subprocess.run(f'/bin/bash -c \'rm -rf /home/deus/.config/waymore/results/{domains_and_or_subdomains_with_their_shared_backends} \' ', shell=True)

# subprocess.run(f'/bin/bash -c \'rm web_resource_to_be_hashed_* \' ', shell=True)
subprocess.run(f'/bin/bash -c \'python3 -m botasaurus.close \' ', shell=True)

# source_counter_output = dict(sorted(source_counter_output.items(), key=operator.itemgetter(1), reverse=True))

# with open(f'source_counter_output','w') as file:
#     for domain,count in source_counter_output.items():
#         file.write(domain + " " + str(count) + "\n")
