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
import shutil

http = urllib3.PoolManager()
whoisxmlapi_keys = ["<auth_key>"]

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

def exit_after_proper_save(file_name, is_exit):
    assets = set()
    with open(file_name) as file:
        for asset in file:
            assets.add(asset.replace("\n",""))
    with open(file_name,'w') as file:
        for asset in assets:
            file.write(asset + "\n")
    if is_exit:
        exit()

def domain_lookup(domain):
    pass

def valid_ip(address):
    try:
        ipaddress.ip_address(address)
        return True
    except:
        return False

# def target_ns_list_manager():
#     domains = open('domains_of_target_and_its_acquisitions')
#     # domain lookup
#     NS_domains = set()
#     for domain in domains:
#         domain = domain.replace("\n","")
#         try:
#             ns_result = dns.resolver.resolve(domain, 'NS')
#             for IPval in ns_result:
#                 NS_domains.add(IPval.to_text()[:-1])
#         except:
#             pass
#         try:
#             soa_result = dns.resolver.resolve(domain, 'SOA')
#             for i in soa_result:
#                 NS_domains.add(re.sub(r"\s.+"," ",str(i))[:-2])
#         except:
#             continue

#     NS_domains = list(NS_domains)
#     # deletion processes
#     common_NS_to_be_ignored = open('/home/deus/targets/common_NS_to_be_ignored','r+')
#     NS_to_be_ignored = open("NS_to_be_ignored", "r+")
#     # automatic deletion
#     for ns in common_NS_to_be_ignored:
#         ns = ns.replace("\n","")
#         if ns in NS_domains:
#             NS_domains.remove(ns)
#     for ns in NS_to_be_ignored:
#         ns = ns.replace("\n","")
#         if ns in NS_domains:
#             NS_domains.remove(ns)

#     # manual deletion

#     for i in range(0, len(NS_domains)):
#         print(f'{i+1}. {NS_domains[i]}')
#     delete_ids = input("number(s) of NSs to delete for any target separated by space if multiple:").split(" ")
#     if not (len(delete_ids) == 1 and delete_ids[0] == ''):
#         for i in range(len(NS_domains),-1,-1):
#             for j in delete_ids:
#                 if int(j) == i+1:
#                     common_NS_to_be_ignored.write(NS_domains[i] + "\n")
#                     common_NS_to_be_ignored.flush()
#                     # fix this below
#                     del NS_domains[i]
#     for i in range(0, len(NS_domains)):
#         print(f'{i+1}. {NS_domains[i]}')
#     delete_ids = input("number(s) of NSs to delete for this target separated by space if multiple:").split(" ")
#     if not (len(delete_ids) == 1 and delete_ids[0] == ''):
#         for i in range(len(NS_domains),-1,-1):
#             for j in delete_ids:
#                 if int(j) == i+1:
#                     NS_to_be_ignored.write(NS_domains[i] + "\n")
#                     NS_to_be_ignored.flush()
#                     # fix this below
#                     del NS_domains[i]
#     common_NS_to_be_ignored.close()
#     NS_to_be_ignored.close()
#     domains.close()
#     return NS_domains

# def target_ms_list_manager():
#     domains = open('domains_of_target_and_its_acquisitions')
#     # domain lookup
#     MS_domains = set()
#     for domain in domains:
#         domain = domain.replace("\n","")
#         try:
#             ms_result = dns.resolver.resolve(domain, 'MX')
#             for IPval in ms_result:
#                 MS_domains.add(re.sub(r".+\s","",IPval.to_text()[:-1]))
#         except:
#             continue

#     MS_domains = list(MS_domains)
#     # deletion processes
#     common_MS_to_be_ignored = open('/home/deus/targets/common_MS_to_be_ignored','r+')
#     MS_to_be_ignored = open("MS_to_be_ignored", "r+")
#     # automatic deletion
#     for ms in common_MS_to_be_ignored:
#         ms = ms.replace("\n","")
#         if ms in MS_domains:
#             MS_domains.remove(ms)
#     for ms in MS_to_be_ignored:
#         ms = ms.replace("\n","")
#         if ms in MS_domains:
#             MS_domains.remove(ms)

#     # manual deletion

#     for i in range(0, len(MS_domains)):
#         print(f'{i+1}. {MS_domains[i]}')
#     delete_ids = input("number(s) of MSs to delete for any target separated by space if multiple:").split(" ")
#     if not (len(delete_ids) == 1 and delete_ids[0] == ''):
#         for i in range(len(MS_domains),-1,-1):
#             for j in delete_ids:
#                 if int(j) == i+1:
#                     common_MS_to_be_ignored.write(MS_domains[i] + "\n")
#                     common_MS_to_be_ignored.flush()
#                     # fix this below
#                     del MS_domains[i]
#     for i in range(0, len(MS_domains)):
#         print(f'{i+1}. {MS_domains[i]}')
#     delete_ids = input("number(s) of MSs to delete for this target separated by space if multiple:").split(" ")
#     if not (len(delete_ids) == 1 and delete_ids[0] == ''):
#         for i in range(len(MS_domains),-1,-1):
#             for j in delete_ids:
#                 if int(j) == i+1:
#                     MS_to_be_ignored.write(MS_domains[i] + "\n")
#                     MS_to_be_ignored.flush()
#                     # fix this below
#                     del MS_domains[i]
#     common_MS_to_be_ignored.close()
#     MS_to_be_ignored.close()
#     domains.close()
#     return MS_domains


def reverse_whois():
    
    print("1. Collect whois chunks")
    print("2. Perform reverse whois")
    print("3. Go back")

    choice = int(input("Choice: "))

    if choice == 1:
        subprocess.Popen(['python3', '/home/deus/scripts/whois_collector.py'],
                     stdout=open('logfile.log', 'a'),
                     stderr=open('logfile.log', 'a'),
                     preexec_fn=os.setpgrp
                     )
    elif choice == 2:
        personal_whois_list = list()
        personal_whois_list_ids_to_be_deleted = list()

        for whois_chunk in open('registrant_info_to_be_used'):
            whois_chunk = whois_chunk.replace("\n","")
            if whois_chunk != "":
                personal_whois_list.append(whois_chunk)
        
        common_whois_chunks_to_be_ignored = open('/home/deus/targets/common_registrant_info_to_be_ignored','r+')
        whois_chunks_to_be_ignored = open("registrant_info_to_be_ignored", "r+")

        # manual deletion
        for i in range(0, len(personal_whois_list)):
            print(f'{i+1}. {personal_whois_list[i]}')

        delete_ids = input("number(s) of whois chunk that's common to multiple companies to delete for any target separated by space if multiple:").split(" ")

        result = list()
        for selected_ids in delete_ids:
            if selected_ids != '':
                result.append(selected_ids)
        delete_ids = result

        delete_ids_new = list()
        for selected_id in delete_ids:
            if '-' in selected_id:
                left_id = selected_id.split("-")[0]
                right_id = selected_id.split("-")[1]
                for i in range(int(left_id), int(right_id) + 1):
                    delete_ids_new.append(i)
            else:
                delete_ids_new.append(selected_id)
        delete_ids = delete_ids_new
    
        if not (len(delete_ids) == 1 and delete_ids[0] == ''):
            for i in range(len(personal_whois_list),-1,-1):
                for j in delete_ids:
                    if int(j) == i+1:
                        common_whois_chunks_to_be_ignored.write(personal_whois_list[i] + "\n")
                        common_whois_chunks_to_be_ignored.flush()
                        personal_whois_list_ids_to_be_deleted.append(i)
                        # del personal_whois_list[i]
        
        for i in range(0, len(personal_whois_list)):
            if i not in personal_whois_list_ids_to_be_deleted:
                print(f'{i+1}. {personal_whois_list[i]}')
        
        delete_ids = input("number(s) of whois chunk that's specific company that isn't of the target or the target itself or a whois search with no result to delete for this target separated by space if multiple:").split(" ")
        
        result = list()
        for selected_ids in delete_ids:
            if selected_ids != '':
                result.append(selected_ids)
        delete_ids = result
        
        delete_ids_new = list()
        for selected_id in delete_ids:
            if '-' in selected_id:
                left_id = selected_id.split("-")[0]
                right_id = selected_id.split("-")[1]
                for i in range(int(left_id), int(right_id) + 1):
                    delete_ids_new.append(i)
            else:
                delete_ids_new.append(selected_id)
        delete_ids = delete_ids_new

        if not (len(delete_ids) == 1 and delete_ids[0] == ''):
            for i in range(len(personal_whois_list),-1,-1):
                for j in delete_ids:
                    if int(j) == i+1:
                        whois_chunks_to_be_ignored.write(personal_whois_list[i] + "\n")
                        whois_chunks_to_be_ignored.flush()
                        personal_whois_list_ids_to_be_deleted.append(i)
                        # del personal_whois_list[i]
        
        personal_whois_list_new = list()
        for i in range(0, len(personal_whois_list)):
            if i not in personal_whois_list_ids_to_be_deleted:
                personal_whois_list_new.append(personal_whois_list[i])
        personal_whois_list = personal_whois_list_new
        
        # automatic chunk that has subchunk deletion
        personal_whois_list_new = list()
        for i in range(0, len(personal_whois_list)):
            whois_chunk = personal_whois_list[i]
            is_the_whois_chunk_a_longer_text_of_short_one = False
            for j in range(0, len(personal_whois_list)):
                if personal_whois_list[j] in whois_chunk and j != i:
                    is_the_whois_chunk_a_longer_text_of_short_one = True
            if not is_the_whois_chunk_a_longer_text_of_short_one:
                personal_whois_list_new.append(whois_chunk)
        personal_whois_list = personal_whois_list_new

        common_whois_chunks_to_be_ignored.close()
        whois_chunks_to_be_ignored.close()

        with open('registrant_info_to_be_used','w') as file:
            for whois_chunk in personal_whois_list:
                file.write(whois_chunk + "\n")
        
        for i in range(0, len(personal_whois_list)):
            print(f'{i+1}. {personal_whois_list[i]}')
        
        print("1. Continue to perform reverse whois")
        print("2. Go back")

        choice = int(input("Choice: "))
        if choice == 1:
            subprocess.Popen(['python3', '/home/deus/scripts/reverse_whois.py'],
                         stdout=open('logfile.log', 'a'),
                         stderr=open('logfile.log', 'a'),
                         preexec_fn=os.setpgrp
                         )
            
            choice_log_file = open("choicelog", "a")
            choice_log_file.write("reverse whois performed\n")
            choice_log_file.close()

        elif choice == 2:
            reverse_whois()
    elif choice == 3:
        horizontal_enum()
    
    
def ip_based_reverse_dns_lookup():

    print("1. Collect ASNs and their IPs")
    print("2. Perform IP based reverse DNS lookup")
    print("3. Go back")

    choice = int(input("Choice: "))

    if choice == 1:
        subprocess.Popen(['python3', '/home/deus/scripts/asn_and_their_ips_collector.py'],
                     stdout=open('logfile.log', 'a'),
                     stderr=open('logfile.log', 'a'),
                     preexec_fn=os.setpgrp
                     )
    elif choice == 2:
        asn_and_its_ips = json.load(open('asn_and_its_ips_to_be_used.json'))
        asns_to_be_deleted = list()

        common_ips_to_be_ignored = open('/home/deus/targets/common_ips_to_be_ignored','r+')
        ips_to_be_ignored = open("ips_to_be_ignored", "r+")

        # manual deletion
        for i in range(0, len(asn_and_its_ips.keys())):
            print(f'{i+1}. AS{list(asn_and_its_ips.keys())[i]}')

        delete_ids = input("number(s) of ASNs to delete for any target separated by space if multiple:").split(" ")

        result = list()
        for selected_ids in delete_ids:
            if selected_ids != '':
                result.append(selected_ids)
        delete_ids = result

        delete_ids_new = list()
        for selected_id in delete_ids:
            if '-' in selected_id:
                left_id = selected_id.split("-")[0]
                right_id = selected_id.split("-")[1]
                for i in range(int(left_id), int(right_id) + 1):
                    delete_ids_new.append(i)
            else:
                delete_ids_new.append(selected_id)
        delete_ids = delete_ids_new

        if not (len(delete_ids) == 1 and delete_ids[0] == ''):
            for i in range(len(asn_and_its_ips.keys()),-1,-1):
                for j in delete_ids:
                    if int(j) == i+1:
                        for ip in asn_and_its_ips[list(asn_and_its_ips.keys())[i]]:
                            common_ips_to_be_ignored.write(ip + "\n")
                            common_ips_to_be_ignored.flush()
                        # del asn_and_its_ips[list(asn_and_its_ips.keys())[i]]
                        asns_to_be_deleted.append(list(asn_and_its_ips.keys())[i])
    
        for i in range(0, len(asn_and_its_ips.keys())):
            if list(asn_and_its_ips.keys())[i] not in asns_to_be_deleted:
                print(f'{i+1}. AS{list(asn_and_its_ips.keys())[i]}')

        delete_ids = input("number(s) of ASNs to delete for this target separated by space if multiple:").split(" ")

        result = list()
        for selected_ids in delete_ids:
            if selected_ids != '':
                result.append(selected_ids)
        delete_ids = result

        delete_ids_new = list()
        for selected_id in delete_ids:
            if '-' in selected_id:
                left_id = selected_id.split("-")[0]
                right_id = selected_id.split("-")[1]
                for i in range(int(left_id), int(right_id) + 1):
                    delete_ids_new.append(i)
            else:
                delete_ids_new.append(selected_id)
        delete_ids = delete_ids_new

        if not (len(delete_ids) == 1 and delete_ids[0] == ''):
            for i in range(len(asn_and_its_ips.keys()),-1,-1):
                for j in delete_ids:
                    if int(j) == i+1:
                        for ip in asn_and_its_ips[list(asn_and_its_ips.keys())[i]]:
                            ips_to_be_ignored.write(ip + "\n")
                            ips_to_be_ignored.flush()
                        # del asn_and_its_ips[list(asn_and_its_ips.keys())[i]]
                        asns_to_be_deleted.append(list(asn_and_its_ips.keys())[i])

        asn_and_its_ips_new = dict()
        for i in range(0, len(asn_and_its_ips.keys())):
            if list(asn_and_its_ips.keys())[i] not in asns_to_be_deleted:
                asn_and_its_ips_new[list(asn_and_its_ips.keys())[i]] = asn_and_its_ips[list(asn_and_its_ips.keys())[i]]
        asn_and_its_ips = asn_and_its_ips_new

        common_ips_to_be_ignored.close()
        ips_to_be_ignored.close()
    
        with open('asn_and_its_ips_to_be_used.json','w') as file:
            file.write(json.dumps(asn_and_its_ips))

        for i in range(0, len(asn_and_its_ips.keys())):
            print(f'{i+1}. AS{list(asn_and_its_ips.keys())[i]}')
        
        print("1. Continue to perform IP based reverse DNS lookup")
        print("2. Go back")

        choice = int(input("Choice: "))
        if choice == 1:
            subprocess.Popen(['python3', '/home/deus/scripts/ip_based_reverse_dns_lookup.py'],
                         stdout=open('logfile.log', 'a'),
                         stderr=open('logfile.log', 'a'),
                         preexec_fn=os.setpgrp
                         )

            choice_log_file = open("choicelog", "a")
            choice_log_file.write("ip based reverse dns lookup performed\n")
            choice_log_file.close()

        elif choice == 2:
            ip_based_reverse_dns_lookup()
    elif choice == 3:
        horizontal_enum()

    
def ssl_grabbing():
    subprocess.Popen(['python3', '/home/deus/scripts/ssl_grabbing.py'],
                 stdout=open('logfile.log', 'a'),
                 stderr=open('logfile.log', 'a'),
                 preexec_fn=os.setpgrp
                 )
def soa_based_reverse_dns_lookup():
    pass
def ns_based_reverse_dns_lookup():
    pass
def ms_based_reverse_dns_lookup():
    pass



def take_screenshot():

    def domains_list_generate(assets):
        with open('domains_to_be_used','w') as file:
            # pattern = "^((?!-))(xn--)?[a-z0-9][a-z0-9-_]{0,61}[a-z0-9]{0,1}\.(xn--)?([a-z0-9\-]{1,61}|[a-z0-9-]{1,30}\.[a-z]{2,})$"
            for asset in assets:
                if valid_subdomain(asset) or valid_domain(asset):
                    file.write(asset + "\n")
    
    assets = asset_list_prepare()

    with open('domains.txt') as file:
        for asset in file:
            asset = asset.replace("\n","")
            if asset != "":
                assets.add(asset)
    
    domains_list_generate(assets)

    subprocess.Popen(['bash', '-c',' [ ! -d "./screenshots" ] && gowitness file -f domains_to_be_used --threads 4 --timeout 10 || gowitness file -f <(comm <( cat domains_to_be_used | sort -u ) <(ls ./screenshots | sed -e s/https-//g -e s/http-//g -e s/.png//g | sort -u) -3) --threads 4 --timeout 10 && gowitness file -f <(comm <( cat domains_to_be_used | sort -u) <(ls ./screenshots | sed -e s/https-//g -e s/http-//g -e s/.png//g | sort -u) -3) --threads 4 --timeout 10 '],
                 stdout=open('logfile.log', 'a'),
                 stderr=open('logfile.log', 'a'),
                 preexec_fn=os.setpgrp
                 )

def passive_subdomain_enum():
    
    subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/subdomains_collector.py'],
                 stdout=open('logfile.log', 'a'),
                 stderr=open('logfile.log', 'a'),
                 preexec_fn=os.setpgrp
                 )

def subdomain_bruteforce():
    
    columns = shutil.get_terminal_size().columns
    print("Uses Cases".center(columns))
    print("1, Enter all to brute force all subdomains in domains.txt")
    print("2, Enter .domain. to find their subdomains and tlds from domains.txt and brute force their subdomains")
    print("3, Enter .domain.tld to find their subdomains from domains.txt and brute force their subdomains")

    domain_or_subdomain = input("Enter a case or multiple cases separated by space: ")

    subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/subdomain_bruteforce.py {domain_or_subdomain}'],
                 stdout=open('logfile.log', 'a'),
                 stderr=open('logfile.log', 'a'),
                 preexec_fn=os.setpgrp
                 )

def tld_enum():
    subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/tld_enum.py'],
                 stdout=open('logfile.log', 'a'),
                 stderr=open('logfile.log', 'a'),
                 preexec_fn=os.setpgrp
                 )

def horizontal_enum():
    while True:

        print("1. Reverse whois")
        print("2. IP based reverse DNS lookup")
        print("3. Go back")

        method_id = int(input("Choice: "))

        if method_id == 1:
            reverse_whois()
        elif method_id == 2:
            ip_based_reverse_dns_lookup()
        elif method_id == 3:
            start()

def vertical_enum():
    while True:

        print("1. TLD enumeration")
        print("2. Passive subdomain enumeration")
        print("3. Subdomain brute force")
        print("4. Go back")

        method_id = int(input("Choice: "))

        if method_id == 1:
            tld_enum()
            choice_log_file = open("choicelog", "a")
            choice_log_file.write("tld enumeration performed\n")
            choice_log_file.close()
        elif method_id == 2:
            passive_subdomain_enum()
            choice_log_file = open("choicelog", "a")
            choice_log_file.write("passive subdomain enumeration performed\n")
            choice_log_file.close()
        elif method_id == 3:
            subdomain_bruteforce()
            choice_log_file = open("choicelog", "a")
            choice_log_file.write("subdomain brute force performed\n")
            choice_log_file.close()
        elif method_id == 4:
            start()

def source_finder():
    while True:
        print("1. Perform CORS based search")
        print("2. Perform keyword/(sub)domain(s) based search on all (sub)domains")
        print("3. Perform sources count")
        print("4. Perform shared external (sub)domain(s) based search on domains with authentication")
        print("5. Perform passive js spidering based on selected (sub)domain(s)")
        print("6. Perform passive url crawling")
        print("7. Perform passive url crawling of pages with form")
        print("8. Go back")

        choice = int(input("Choice: "))

        if choice == 1:
            subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/cors_based.py'],
                         stdout=open('logfile.log', 'a'),
                         stderr=open('logfile.log', 'a'),
                         preexec_fn=os.setpgrp
                         )
        elif choice == 2:
            columns = shutil.get_terminal_size().columns
            print("Uses Cases".center(columns))
            print("1, Enter all to find the sources of all domains")
            print("2, Enter *.domain.tld or domain.* to find their sources")
            print("3, Enter string(domain name only for example) to find the sources that hold that text")
            print("4, Enter domain that you want its sources to be found")
            domain_or_subdomain = input("Enter a case or multiple cases separated by space: ")
            subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/source_based.py {domain_or_subdomain}'],
                         stdout=open('logfile.log', 'a'),
                         stderr=open('logfile.log', 'a'),
                         preexec_fn=os.setpgrp
                         )
            
            choice_log_file = open("choicelog", "a")
            choice_log_file.write("keyword/(sub)domain(s) based source finder performed\n")
            choice_log_file.close()
        elif choice == 3:
            subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/source_counter.py'],
                         stdout=open('logfile.log', 'a'),
                         stderr=open('logfile.log', 'a'),
                         preexec_fn=os.setpgrp
                         )
            choice_log_file = open("choicelog", "a")
            choice_log_file.write("source counter performed\n")
            choice_log_file.close()
        elif choice == 4:
            columns = shutil.get_terminal_size().columns
            print("Uses Cases".center(columns))
            print("1, Enter all to find the sources of all domains with authentication keyword")
            print("2, Enter *.domain with authentication keyword we get from domains_with_authentication to find the source of all *.domain")
            print("3, Enter a shared domain that you want its sources to be found")

            domain_or_subdomain = input("Enter a case or multiple cases separated by space: ")

            subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/source_based.py subdomains_with_authentication {domain_or_subdomain}'],
                         stdout=open('logfile.log', 'a'),
                         stderr=open('logfile.log', 'a'),
                         preexec_fn=os.setpgrp
                         )
            choice_log_file = open("choicelog", "a")
            choice_log_file.write("performed shared external (sub)domain(s) based search on (sub)domain(s) with authentication \n")
            choice_log_file.close()
        elif choice == 5:
            columns = shutil.get_terminal_size().columns
            print("Uses Cases".center(columns))
            print("1, Enter all /api/v1 /api/v2 param1,param2 to find /api/v1 and /api/v2 and parameters param1 and param2 together in the sources of all domains")
            print("2, Enter subtarget /api/v1 /api/v2 param1,param2 to find /api/v1 and /api/v2 and parameters param1 and param2 together in the sources of all domains in all_subtarget_domains.txt of this subtarget")
            print("3, Enter *.domain.* /api/v1 /api/v2 param1,param2 to find /api/v1 and /api/v2 and parameters param1 and param2 together in the sources of all domains that have .domain.")
            print("4, Enter *.domain.tld /api/v1 /api/v2 param1,param2 to find /api/v1 and /api/v2 and parameters param1 and param2 together in the sources of all domains that have .domain.tld")
            print("5, Enter (subdomain.)domain.tld /api/v1 /api/v2 param1,param2 to find /api/v1 and /api/v2 and parameters param1 and param2 together in the sources of all domains that have (subdomain.)domain.tld")

            domain_or_subdomain_with_paths = input("Enter a case: ")

            subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/source_based.py api_based_search {domain_or_subdomain_with_paths}'],
                         stdout=open('logfile.log', 'a'),
                         stderr=open('logfile.log', 'a'),
                         preexec_fn=os.setpgrp
                         )
            choice_log_file = open("choicelog", "a")
            choice_log_file.write(f"passive js spidering with {domain_or_subdomain_with_paths} argument(s) performed \n")
            choice_log_file.close()
        elif choice == 6:

            columns = shutil.get_terminal_size().columns
            print("Uses Cases".center(columns))
            print("1, Enter all to get urls of hosts in collected_domains.txt")
            print("2, Enter subtarget to get urls of hosts in all_subtarget_domains.txt of this subtarget")
            print("3, Enter *.domain.tld to get urls of hosts that have .domain.tld in collected_domains.txt")
            print("4, Enter a host to get its urls")

            domain_or_subdomain = input("Enter a case or multiple cases separated by space: ")

            subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/passive_url_crawler.py {domain_or_subdomain}'],
                         stdout=open('logfile.log', 'a'),
                         stderr=open('logfile.log', 'a'),
                         preexec_fn=os.setpgrp
                         )
            
            choice_log_file = open("choicelog", "a")
            choice_log_file.write("passive url crawler performed\n")
            choice_log_file.close()
        elif choice == 7:
            columns = shutil.get_terminal_size().columns
            print("Uses Cases".center(columns))
            print("1, Enter all to get urls of pages with forms in all domains")
            print("2, Enter subtarget to get urls of pages with forms of hosts in all_subtarget_domains.txt of this subtarget")
            print("3, Enter *.domain.* to get urls of pages with forms in all domains that have .domain.")
            print("4, Enter *.domain.tld to get urls of pages with forms in all domains that have .domain.tld")
            print("5, Enter (subdomain.)domain.tld to get urls of pages with forms to that specific (sub)domain")

            domain_or_subdomain_with_paths = input("Enter a case: ")
            subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/source_based.py html_based_search {domain_or_subdomain_with_paths}'],
                         stdout=open('logfile.log', 'a'),
                         stderr=open('logfile.log', 'a'),
                         preexec_fn=os.setpgrp
                         )
            choice_log_file = open("choicelog", "a")
            choice_log_file.write(f"passive html spidering with {domain_or_subdomain_with_paths} argument(s) performed\n")
            choice_log_file.close()
        elif choice == 8:
            start()

def similar_backend_finder():
    while True:
        print("1. Perform searching for similar backends with subdomain and domain names")
        print("2. Perform searching for similar backends on web apps with authentications")
        print("3. Go back")

        choice = int(input("Choice: "))

        if choice == 1:
            domains_and_or_subdomains = input("Enter subdomain or wildcard as subdomain like *.domain.tld i should find similar backend to it/them: ")
            subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/shared_backend_finder.py {domains_and_or_subdomains}'],
                         stdout=open('logfile.log', 'a'),
                         stderr=open('logfile.log', 'a'),
                         preexec_fn=os.setpgrp
                         )
        elif choice == 2:
            columns = shutil.get_terminal_size().columns
            print("Uses Cases".center(columns))
            print("1, Enter *.domain with authentication keywords we get from domains_with_authentication to find their shared backends")
            print("2, Enter domain with authentication keywords you want its shared backend to be found")

            domain_or_subdomain = input("Enter a case or multiple cases separated by space: ")

            subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/shared_backend_finder.py subdomains_with_authentication {domain_or_subdomain}'],
                         stdout=open('logfile.log', 'a'),
                         stderr=open('logfile.log', 'a'),
                         preexec_fn=os.setpgrp
                         )
        elif choice == 3:
            start()
        
        if choice == 1 or choice == 2:
            choice_log_file = open("choicelog", "a")
            choice_log_file.write("performed similar backend finder\n")
            choice_log_file.close()


def web_app_with_authentication_finder():
    # domains_and_or_subdomains = input("Enter all to search for authentication page in all of domains or Enter sub to search for authentication page in all of subdomains of domains that are found with all: ")
    
    # while domains_and_or_subdomains != "all" and domains_and_or_subdomains != "sub":
    #     domains_and_or_subdomains = input("Enter all to search for authentication page in all of domains or Enter sub to search for authentication page in all of subdomains of domains that are found with all: ")
    
    subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/web_app_with_authentication_finder.py'],
                 stdout=open('logfile.log', 'a'),
                 stderr=open('logfile.log', 'a'),
                 preexec_fn=os.setpgrp
                 )
    
    choice_log_file = open("choicelog", "a")
    choice_log_file.write("performed domains/subdomains with authentication finder\n")
    choice_log_file.close()

def find_origin_ip():

    columns = shutil.get_terminal_size().columns

    print("Uses Cases".center(columns))
    print("1, Enter all <url> to use all collected hostnames for finding the origin of the url's hostname")
    print("2, Enter *.domain.* <url> to use all collected hostnames that have .domain. for finding the origin of the url's hostname")
    print("3, Enter *.domain.tld <url> to use all collected hostnames that have .domain.tld for finding the origin of the url's hostname")
    print("4, Enter hostname <url> to use hostname for finding the origin of the url's hostname")

    server_origin_finder_input = input("Enter a case: ")

    subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/server_origin_finder.py {server_origin_finder_input}'],
                 stdout=open('logfile.log', 'a'),
                 stderr=open('logfile.log', 'a'),
                 preexec_fn=os.setpgrp
                 )

def start():
    subprocess.run(['bash', '-c',f'python3 /home/deus/scripts/setup_proxy.py'],
                 stdout=open('logfile.log', 'a'),
                 stderr=open('logfile.log', 'a')
                 )
    while True:

        print("1. Horizontal Enumeration")
        print("2. Vertical Enumeration")
        print("3. SSL/TLS grabbing")
        print("4. Find web apps with authentication")
        print("5. Find shared backend")
        print("6. Web source finder")
        print("7. Find origin IP")
        print("8. Take Screenshots of domains and subdomains amassed using the above methods")
        print("9. Exit")

        choice = int(input("Choice: "))

        if choice == 1:
            horizontal_enum()
        elif choice == 2:
            vertical_enum()
        elif choice == 3:
            ssl_grabbing()
        elif choice == 4:
            web_app_with_authentication_finder()
        elif choice == 5:
            similar_backend_finder()
        elif choice == 6:
            source_finder()
        elif choice == 7:
            find_origin_ip()
        elif choice == 8:
            take_screenshot()
        elif choice == 9:
            exit()

start()