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
from urllib.parse import urlparse

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
    with open('./../assets_of_target_and_its_acquisitions') as file:
        for asset in file:
            asset = asset.replace("\n","")
            if asset != "":
                assets.add(asset)
    with open('./../reverse_whois_output') as file:
        for asset in file:
            asset = asset.replace("\n","")
            if asset != "":
                assets.add(asset)
    with open('./../IP_based_reverse_dns_output') as file:
        for asset in file:
            asset = asset.replace("\n","")
            if asset != "":
                assets.add(asset)
    with open('./../ssl_certificate_grabbing_output') as file:
        for asset in file:
            asset = asset.replace("\n","")
            if asset != "":
                assets.add(asset)
    with open('./../tld_enum_output') as file:
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
links_with_auth_keywords = manager.list()
urls_output_lock = multiprocessing.Lock()

domains = manager.list()

authentication_keywords = ["login","signin","sign-in","sign in","log in","log-in","register","sign-up","signup","sign up","auth"]
add_subs = False

# with open("logfile.log", "a") as file:
#     for i in range(1, len(sys.argv)):
#         file.write(str(sys.argv[i]) + "\n")
# exit()

# sublinks_with_auth_keywords = set()

domains_list = set()
with open('./../domains.txt') as file:
    for domain in file:
        domain = domain.replace("\n","")
        domains_list.add(domain)

# def collect_subdomains_and_domains_with_possible_authentication(domain_with_authentication):
#     global domains
#     global sublinks_with_auth_keywords
#     global domains_list

#     domain_with_dot_at_first = "." + domain_with_authentication
    
#     for domain in domains_list:
#         if domain_with_dot_at_first in domain and domain_with_dot_at_first[-2:] == domain[-2:] and domain not in sublinks_with_auth_keywords:
#             domains.append(domain)
    
#     for domain in domain_list_prepare():
#         if domain_with_authentication == domain:
#             domains.append(domain)


# if sys.argv[1] == "all":
domains = set()

for domain in domain_list_prepare():
    domains.add(domain)
with open('./../domains.txt') as file:
    for domain in file:
        domain = domain.replace("\n","")
        domains.add(domain)

# links_with_auth_keywords_file = set()
# if os.path.exists('sublinks_with_auth_keywords'):
#     with open('sublinks_with_auth_keywords') as file:
#         for domain in file:
#             domain = domain.replace("\n","")
#             links_with_auth_keywords_file.add(domain)

# domains = domains - links_with_auth_keywords_file

    # add_subs = True
# elif sys.argv[1] == "sub":
#     links_with_auth_keywords_file = set()

#     with open('links_with_auth_keywords') as file:
#         for domain in file:
#             domain = domain.replace("\n","")
#             links_with_auth_keywords_file.add(domain)
    
#     links_with_auth_keywords_file = list(links_with_auth_keywords_file)

#     if os.path.exists('./sublinks_with_auth_keywords'):
#         with open('sublinks_with_auth_keywords') as file:
#             for domain in file:
#                 domain = domain.replace("\n","")
#                 if domain_with_dot_at_first in domain:
#                     sublinks_with_auth_keywords.add(domain)

#     pool = multiprocessing.Pool(4)
#     pool.map(collect_subdomains_and_domains_with_possible_authentication, links_with_auth_keywords_file, chunksize=1)


# for i in range(1, len(sys.argv)):
#     if "all" == sys.argv[i]:
#         domains = set()
        
#         for domain2 in domain_list_prepare():
#             with open('domains.txt') as file:
#                 for domain in file:
#                     domain = domain.replace("\n","")
#                     if domain2 in domain:
#                         domains.add(domain2)
#                         break
        
#         links_with_auth_keywords_file = set()
#         if os.path.exists(f'./links_with_auth_keywords'):
#             with open('links_with_auth_keywords') as file:
#                 for domain in file:
#                     domain = domain.replace("\n","")
#                     links_with_auth_keywords_file.add(domain)
        
#         domains = domains - links_with_auth_keywords_file
#         domains = list(domains)
        
#         add_subs = True
#     elif "*" in sys.argv[i]:
#         sublinks_with_auth_keywords = set()
#         domain_without_wildcard = sys.argv[i].replace("*","")
#         domain_without_wildcard_and_dot = sys.argv[i].replace("*.","")

#         if os.path.exists(f'./sublinks_with_auth_keywords'):
#             with open('sublinks_with_auth_keywords') as file:
#                 for domain in file:
#                     domain = domain.replace("\n","")
#                     if domain_without_wildcard in domain:
#                         sublinks_with_auth_keywords.add(domain)
        
#         with open('domains.txt') as file:
#             for domain in file:
#                 domain = domain.replace("\n","")
#                 if domain_without_wildcard in domain and domain not in sublinks_with_auth_keywords:
#                     domains.add(domain)
        
#         # sys.argv[i] = sys.argv[i].replace("*.","")
#         for domain in domain_list_prepare():
#             if domain_without_wildcard_and_dot == domain:
#                 domains.add(domain)

# log_file = open("logfile.log", "a")
# log_file.write(str(domains) + "\n")
# log_file.close()

# exit()

domains = list(domains)
domains_len = len(domains)

def source_identifier(domain):
    global links_with_auth_keywords
    global domains
    global domains_len
    global counter
    global proxies
    global used_proxies_across_processes
    global authentication_keywords
    global manager
    global urls_output_lock
    
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
                # if add_subs:
                #     subprocess.run(f' bash -c \' waymore -i {domain} -mode B -r 2 -p 3 -xcc &> waymore_output_{index_of_domain}.txt \' ', shell=True, capture_output=True, text=True, timeout=2000)
                # else:
                subprocess.run(f' bash -c \' waymore -i {domain} -mode B -r 2 -p 3 -xcc -url-filename -c ~/documents/html_resources_config.yml &> waymore_output_{index_of_domain}.txt \' ', shell=True, capture_output=True, text=True, timeout=2000)
            except subprocess.TimeoutExpired:
                timeout_count += 1
        else:
            try:
                # if add_subs:
                #     subprocess.run(f' bash -c \' proxychains4 -f /home/deus/documents/{proxy} -q waymore -i {domain} -mode B -r 2 -p 3 -xcc &> waymore_output_{index_of_domain}.txt \' ', shell=True, capture_output=True, text=True, timeout=2000)
                # else:
                subprocess.run(f' bash -c \' proxychains4 -f /home/deus/documents/{proxy} -q waymore -i {domain} -mode B -r 2 -p 3 -xcc -url-filename -c ~/documents/html_resources_config.yml &> waymore_output_{index_of_domain}.txt \' ', shell=True, capture_output=True, text=True, timeout=2000)
            except subprocess.TimeoutExpired:
                timeout_count += 1
        
        condition_of_waymore_output = subprocess.run(f'/bin/bash -c \'tail -n 100 waymore_output_{index_of_domain}.txt \' ', shell=True, capture_output=True, text=True).stdout
        if "100.0% Complete" in condition_of_waymore_output or "No archived responses were found" in condition_of_waymore_output or timeout_count == 2:
            # domains_which_sources_we_have_collected = open("domains_which_sources_we_have_collected", "a")
            # domains_which_sources_we_have_collected.write(domain + "\n")
            # domains_which_sources_we_have_collected.close()
            used_proxies_across_processes.remove(proxy)
            break
        failure_count += 1
        error_count = open("error_count", "a")
        error_count.write(proxy + " " + domain + " "  + str(failure_count) + "\n")
        error_count.close()
        if failure_count > 2:
            used_proxies_across_processes.remove(proxy)
            break
        time.sleep(60)
    
    subprocess.run(f'/bin/bash -c \'rm waymore_output_{index_of_domain}.txt \' ', shell=True)

    def is_the_authentication_keyword_in_content(content, desired_domain):
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
            should_i_break_too = False
            added_count = 0
            for authentication_keyword in authentication_keywords:
                for file_name in downloaded_files_of_domain:
                    # try:
                    output = subprocess.run(f' bash -c \' grep -i -I "{authentication_keyword}" /home/deus/.config/waymore/results/{domain}/{file_name} \'  ', shell=True, capture_output=True, text=True, timeout=60).stdout.lower()
                    
                    link = filename_processor(file_name)
                    if authentication_keyword in output and link not in links_with_auth_keywords:
                        added_count += 1
                        links_with_auth_keywords.append(link)

                        with urls_output_lock:
                            with open('links_with_auth_keywords','a') as file:
                                file.write(link + "\n")
                            
                            if authentication_keyword in ["register","sign-up","signup","sign up"]:
                                with open('links_with_reg_keywords','a') as file:
                                    file.write(link + "\n")
                            
                        if added_count == 10:
                            should_i_break_too = True
                            break
                    # except:
                    #     pass
                if should_i_break_too:
                    break
    # except:
    #     pass

    # log_file = open("logfile.log", "a")
    # log_file.write(proxy + " here3" + "\n")
    # log_file.close()
    
    subprocess.run(f'/bin/bash -c \'rm -rf /home/deus/.config/waymore/results/{domain} \' ', shell=True)
    
    log_file = open("logfile.log", "a")
    log_file.write("Finished " + str(counter.value) + "/" + str(domains_len) + "\n")
    log_file.close()
    with counter.get_lock():
        counter.value += 1

subprocess.run(f'/bin/bash -c \'rm waymore_output_*.txt \' ', shell=True)

pool = multiprocessing.Pool(len(proxies))
pool.map(source_identifier, domains, chunksize=1)

# new_links_with_auth_keywords = dict()
# for key,value in links_with_auth_keywords.items():
#     new_links_with_auth_keywords[key] = list(value)
subdomains_with_authentication = list()
for url in links_with_auth_keywords:
    hostname = urlparse(url).hostname
    if hostname not in subdomains_with_authentication:
        subdomains_with_authentication.append(hostname)
# if add_subs:
with open('subdomains_with_authentication','a') as file:
    for hostname in subdomains_with_authentication:
        file.write(hostname + "\n")
# else:

