
import multiprocessing
try:
   multiprocessing.set_start_method('fork', force=True)
   print("forked")
except RuntimeError:
    print("unable to fork!")
    exit()
import subprocess
import os
import math
import time
import re

tlds = {'zip', 'llc', 'memorial', 'cpa', 'barclays', 'dz', 'accountant', 'temasek', 'mattel', 'site', 'tt', 'solar', 'ricoh', 'km', 'kyoto', 'haus', 'baidu', 'jetzt', 'flickr', 'ally', 'management', 'xn--pssy2u', 'engineer', 'allstate', 'garden', 'xn--rhqv96g', 'forsale', 'organic', 'estate', 'rentals', 'surgery', 'gmo', 'mt', 'baseball', 'buzz', 'rugby', 'design', 'shangrila', 'delta', 'gt', 'food', 'restaurant', 'redumbrella', 'lundbeck', 'by', 'af', 'dk', 'barefoot', 'page', 'vegas', 'hyundai', 'pn', 'softbank', 'mr', 'review', 'gh', 'afl', 'jp', 'recipes', 'monash', 'airforce', 'ferrero', 'academy', 'hbo', 'tc', 'capital', 'xn--3bst00m', 'shaw', 'leclerc', 'sl', 'xn--42c2d9a', 'me', 'sn', 'voyage', 'citadel', 'ping', 'bi', 'erni', 'seek', 'yun', 'asda', 'shell', 'wiki', 'baby', 'dot', 'eu', 'fly', 'hospital', 'goodyear', 'anz', 'vanguard', 'insurance', 'kr', 'zw', 'tz', 'xn--otu796d', 'travelersinsurance', 'ai', 'photo', 'africa', 'loan', 'otsuka', 'tickets', 'gdn', 'vana', 'sd', 'ie', 'schaeffler', 'tn', 'legal', 'money', 'xn--xkc2dl3a5ee0h', 'iq', 'marshalls', 'voto', 'ae', 'cv', 'lexus', 'sex', 'sexy', 'jewelry', 'sew', 'quest', 'dclk', 'xn--6qq986b3xl', 'dvr', 'discount', 'hotmail', 'yachts', 'toshiba', 'barcelona', 'suzuki', 'hk', 'yokohama', 'email', 'gripe', 'hair', 'aeg', 'bike', 'man', 'skype', 'ing', 'city', 'aarp', 'accenture', 'abc', 'fi', 'cipriani', 'xn--flw351e', 'uz', 'ge', 'natura', 'xn--mgbca7dzdo', 'extraspace', 'events', 'read', 'sharp', 'amazon', 'forum', 'investments', 'beauty', 'prod', 'vn', 'gl', 'click', 'immobilien', 'vote', 'chase', 'netflix', 'smile', 'ss', 'abb', 'silk', 'tattoo', 'jot', 'horse', 'chrome', 'international', 'ifm', 'company', 'hyatt', 'amex', 'xn--j1amh', 'army', 'mma', 'ltd', 'hotels', 'homes', 'vacations', 'do', 'university', 'auto', 'kg', 'stockholm', 'claims', 'film', 'xn--j6w193g', 'wedding', 'versicherung', 'am', 'xn--5tzm5g', 'social', 'im', 'diet', 'tushu', 'eurovision', 'uk', 'george', 'book', 'hamburg', 'faith', 'xn--d1alf', 'theatre', 'open', 'sanofi', 'uno', 'dabur', 'audible', 'lawyer', 'pin', 'sbi', 'holiday', 'sucks', 'citic', 'xn--nyqy26a', 'xn--4dbrk0ce', 'bentley', 'xn--fiq228c5hs', 'physio', 'as', 'nc', 'tienda', 'nab', 'xn--9et52u', 'guru', 'bank', 'business', 'engineering', 'grainger', 'dish', 'diamonds', 'amfam', 'rehab', 'bbc', 'office', 'save', 'analytics', 'sener', 'free', 'xn--fzc2c9e2c', 'ms', 'la', 'delivery', 'kids', 'xn--kprw13d', 'sv', 'lease', 'jio', 'cyou', 'taxi', 'ax', 'itau', 'tiaa', 'ipiranga', 'xn--fiqz9s', 'xn--node', 'network', 'xn--90ais', 'lotto', 'es', 'webcam', 'pw', 'xxx', 'bm', 'xn--80asehdb', 'xn--tckwe', 'compare', 'safety', 'pramerica', 'blog', 'hitachi', 'fox', 'earth', 'center', 'yt', 'actor', 'makeup', 'desi', 'xn--45br5cyl', 'xn--vermgensberatung-pwb', 'luxe', 'pccw', 'best', 'cm', 'cz', 'ren', 'xn--tiq49xqyj', 'jobs', 'kim', 'vision', 'mit', 'jo', 'rip', 'music', 'secure', 'car', 'nissan', 'smart', 'nowruz', 'school', 'xn--ngbe9e0a', 'sh', 'maison', 'lifestyle', 'comcast', 'mls', 'ao', 'brother', 'nissay', 'bond', 'new', 'kz', 'bzh', 'domains', 'lighting', 'lego', 'boehringer', 'attorney', 'barclaycard', 'kred', 'java', 'fish', 'market', 'be', 'cool', 'jeep', 'kerryproperties', 'life', 'sling', 'yamaxun', 'tr', 'travel', 'lamer', 'cologne', 'tatamotors', 'kw', 'drive', 'dental', 'xn--3ds443g', 'flights', 'pioneer', 'hm', 'pf', 'sncf', 'pm', 'progressive', 'mango', 'racing', 'mc', 'cc', 'ky', 'finance', 'si', 'singles', 'axa', 'cooking', 'virgin', 'vlaanderen', 'lancaster', 'mp', 'cloud', 'sarl', 'cn', 'soy', 'productions', 'healthcare', 'xn--9krt00a', 'xn--gk3at1e', 'fido', 'arab', 'immo', 'bt', 'xn--11b4c3d', 'honda', 'scholarships', 'abogado', 'epson', 'xn--o3cw4h', 'aero', 'cd', 'co', 'family', 'ice', 'wolterskluwer', 'skin', 'aaa', 'xn--3e0b707e', 'sandvik', 'ruhr', 'rw', 'sony', 'pub', 'fit', 'coach', 'cars', 'plumbing', 'download', 'poker', 'amica', 'run', 'spa', 'buy', 'hr', 'salon', 'xn--1ck2e1b', 'farmers', 'dad', 'comsec', 'kp', 'monster', 'doctor', 'beats', 'aw', 'ac', 'xn--czru2d', 'grocery', 'med', 'alipay', 'guge', 'surf', 'airbus', 'tours', 'zara', 'xn--c1avg', 'ls', 'goldpoint', 'juniper', 'kuokgroup', 'realtor', 'xn--kcrx77d1x4a', 'aramco', 'fo', 'xn--qxa6a', 'xn--xhq521b', 'love', 'cleaning', 'xn--e1a4c', 'yahoo', 'juegos', 'nr', 'frogans', 'gratis', 'broadway', 'goo', 'xin', 'kh', 'land', 'xihuan', 'citi', 'nokia', 'like', 'dev', 'report', 'xn--h2breg3eve', 'mom', 'olayangroup', 'xn--q7ce6a', 'ad', 'stream', 'latrobe', 'dog', 'gallup', 'press', 'calvinklein', 'vu', 'mw', 'gold', 'cruises', 'athleta', 'commbank', 'gal', 'tube', 'play', 'sz', 'xn--54b7fta0cc', 'career', 'org', 'tax', 'app', 'koeln', 'lu', 'call', 'broker', 'net', 'photography', 'shoes', 'tci', 'boston', 'world', 'bio', 'weber', 'supplies', 'verisign', 'ye', 'rogers', 'dj', 'it', 'security', 'aetna', 'kn', 'energy', 'vi', 'joburg', 'xn--mgbai9azgqp6j', 'xn--gecrj9c', 'samsclub', 'intuit', 'moi', 'xn--pgbs0dh', 'bbva', 'space', 'sport', 'ht', 'media', 'bingo', 'news', 'flir', 'republican', 'accountants', 'stada', 'case', 'fidelity', 'bridgestone', 'fun', 'trading', 'bargains', 'xn--qxam', 'itv', 'realestate', 'zone', 'wien', 'nec', 'ollo', 'gap', 'ventures', 'xn--p1acf', 'emerck', 'date', 'to', 'np', 'dupont', 'ws', 'omega', 'wanggou', 'mg', 'diy', 'sa', 'ceo', 'mtn', 'na', 'kddi', 'xn--j1aef', 'mitsubishi', 'dell', 'author', 'samsung', 'homesense', 'gf', 'durban', 'help', 'ck', 'bar', 'nyc', 'church', 'trv', 'lotte', 'movie', 'tw', 'youtube', 'qa', 'win', 'xn--zfr164b', 'parts', 'men', 'ci', 'jm', 'xn--1qqw23a', 'miami', 'lat', 'americanexpress', 'pics', 'pohl', 'apple', 'furniture', 'tdk', 'windows', 'latino', 'statefarm', 'auspost', 'contact', 'democrat', 'nike', 'pars', 'select', 'schwarz', 'vip', 'consulting', 'voting', 'edeka', 'lipsy', 'stc', 'creditcard', 'je', 'williamhill', 'prime', 'courses', 'xn--ygbi2ammx', 'dunlop', 'wine', 'motorcycles', 'landrover', 'xn--s9brj9c', 'ro', 'credit', 'clinique', 'playstation', 'gi', 'xn--hxt814e', 'bz', 'deloitte', 'coupon', 'saxo', 'prof', 'bet', 'mo', 'praxi', 'lasalle', 'homedepot', 'al', 'map', 'edu', 'soccer', 'il', 'er', 'vg', 'xn--mgb9awbf', 'bible', 'paris', 'xn--imr513n', 'got', 'gucci', 'orange', 'archi', 'eat', 'netbank', 'ug', 'schmidt', 'nico', 'ag', 'construction', 'feedback', 'xn--cck2b3b', 'flowers', 'xn--mgberp4a5d4ar', 'frl', 'xn--cg4bki', 'bbt', 'xn--80aqecdr1a', 'mobile', 'avianca', 'bh', 'red', 'pl', 'xn--9dbq2a', 'channel', 'ftr', 'software', 'place', 'xn--mgbgu82a', 'xn--w4r85el8fhu5dnra', 'exposed', 'yandex', 'agakhan', 'bosch', 'globo', 'staples', 'capetown', 'beer', 'frontier', 'va', 'caravan', 'gov', 'uy', 'abudhabi', 'arpa', 'search', 'xn--c2br7g', 'tl', 'yodobashi', 'vet', 'mz', 'lacaixa', 'target', 'villas', 'rexroth', 'hkt', 'tools', 'asia', 'contractors', 'viking', 'xn--mgbc0a9azcg', 'pro', 'ril', 'art', 'coupons', 'kpmg', 'xn--vuq861b', 'dds', 'meme', 'jnj', 'nz', 'website', 'tirol', 'abbvie', 'condos', 'lplfinancial', 'sina', 'xn--czr694b', 'unicom', 'gq', 'americanfamily', 'careers', 'xn--wgbl6a', 'bestbuy', 'eg', 'xn--fpcrj9c3d', 'gmx', 'properties', 'cl', 'bharti', 'ubank', 'wtc', 'lk', 'mx', 'xn--lgbbat1ad8j', 'xn--3hcrj9c', 'corsica', 'rs', 'hu', 'bayern', 'adult', 'xn--h2brj9c', 'wtf', 'florist', 'codes', 'xn--mgbtx2b', 'xn--mgbah1a3hjkrd', 'shiksha', 'lol', 'theater', 'xn--czrs0t', 'nexus', 'xn--unup4y', 'viajes', 'gbiz', 'xn--45brj9c', 'limited', 'sbs', 'xn--gckr3f0f', 'bo', 'ch', 'ford', 'eus', 'ninja', 'hosting', 'education', 'town', 'bot', 'catholic', 'nfl', 'ski', 'scb', 'able', 'st', 'bom', 'rest', 'charity', 'au', 'how', 'ke', 'supply', 'xn--6frz82g', 'pnc', 'xn--mgbx4cd0ab', 'agency', 'xn--4gbrim', 'dating', 'xn--i1b6b1a6a2e', 'xn--jvr189m', 'ba', 'bb', 'ne', 'audi', 'xn--80aswg', 'glass', 'plus', 'kpn', 'xn--mgbpl2fh', 'xn--eckvdtc9d', 'ggee', 'vc', 'gy', 'ooo', 'xn--ngbrx', 'blockbuster', 'trade', 'toys', 'swiss', 'xn--mgbt3dhd', 'bnpparibas', 'toyota', 'digital', 'mini', 'kfh', 'xn--fjq720a', 'tkmaxx', 'xn--qcka1pmc', 'neustar', 'viva', 'apartments', 'aol', 'xn--io0a7i', 'visa', 'nrw', 'tel', 'ott', 'allfinanz', 'dhl', 'xfinity', 'phone', 'om', 'fishing', 'xn--8y0a063a', 'aig', 'data', 'cash', 'nba', 'enterprises', 'community', 'college', 'mn', 'br', 'hermes', 'locker', 'shop', 'game', 'works', 'booking', 'show', 'philips', 'ph', 'hiv', 'ads', 'cal', 'cfa', 'guide', 'lt', 'ua', 'meet', 'ngo', 'xn--5su34j936bgsg', 'bf', 'kindle', 'casa', 'xn--2scrj9c', 'xn--p1ai', 'tech', 'clothing', 'guardian', 'chat', 'xn--nqv7fs00ema', 'pa', 'istanbul', 'xn--55qx5d', 'associates', 'basketball', 'dentist', 'xn--g2xx48c', 'hot', 'xn--vhquv', 'xn--mix891f', 'woodside', 'canon', 'xbox', 'dealer', 'de', 'godaddy', 'xn--mgbi4ecexp', 'uol', 'xn--cckwcxetd', 'nextdirect', 'cw', 'fail', 'boats', 'style', 'thd', 'financial', 'cat', 'pwc', 'bostik', 'gift', 'xn--mgba3a4f16a', 'xn--vermgensberater-ctb', 'farm', 'cx', 'reisen', 'aq', 'partners', 'tips', 'cafe', 'moe', 'prudential', 'fairwinds', 'walter', 'luxury', 'bauhaus', 'crs', 'gd', 'gw', 'here', 'pharmacy', 'int', 'th', 'pt', 'za', 'oracle', 'loans', 'su', 'richardli', 'law', 'msd', 'shia', 'locus', 'protection', 'banamex', 'hdfcbank', 'tvs', 'foundation', 'taipei', 'rent', 'anquan', 'name', 'nowtv', 'rodeo', 'gu', 'ml', 'camp', 'quebec', 'host', 'ieee', 'ist', 'io', 'xn--mgbbh1a', 'circle', 'sb', 'sc', 'whoswho', 'gr', 'green', 'menu', 'gallery', 'fk', 'xn--rovu88b', 'hughes', 'berlin', 'gn', 'pet', 'akdn', 'discover', 'porn', 'fan', 'firmdale', 'mint', 'xn--l1acc', 'cards', 'ee', 'industries', 'chanel', 'sandvikcoromant', 've', 'cfd', 'olayan', 'catering', 'post', 'tatar', 'cy', 'md', 'sk', 'blue', 'google', 'storage', 'id', 'kerrylogistics', 'onl', 'eco', 'icu', 'tm', 'cr', 'moto', 'reise', 'airtel', 'politie', 'box', 'fans', 'ir', 'fujitsu', 'giving', 'pr', 'zero', 'cab', 'xn--fzys8d69uvgm', 'fyi', 'xn--45q11c', 'alstom', 'kitchen', 'se', 'ar', 'xn--xkc2al3hye2a', 'xyz', 'fage', 'store', 'video', 'ec', 'gp', 'observer', 'sale', 'day', 'kiwi', 'osaka', 'sj', 'xn--mxtq1m', 'nagoya', 'firestone', 'christmas', 'jcb', 'rsvp', 'my', 'xn--jlq480n2rg', 'institute', 'esq', 'mov', 'imamat', 'rocks', 'inc', 'obi', 'gay', 'tg', 'xn--ses554g', 'nf', 'sx', 'hiphop', 'krd', 'tennis', 'gifts', 'tunes', 'realty', 'goog', 'irish', 'mckinsey', 'xn--t60b56a', 'travelers', 'ca', 'cisco', 'limo', 're', 'docs', 'technology', 'audio', 'joy', 'team', 'mq', 'cf', 'xn--mgbaam7a8h', 'winners', 'xn--fhbei', 'xn--mgbbh1a71e', 'deal', 'is', 'sydney', 'xn--mgbcpq6gpa1a', 'mk', 'tjmaxx', 'jmp', 'sg', 'lilly', 'lc', 'li', 'jll', 'arte', 'xn--yfro4i67o', 'services', 'wf', 'creditunion', 'exchange', 'nra', 'mobi', 'ismaili', 'casino', 'cymru', 'xn--q9jyb4c', 'talk', 'support', 'mba', 'online', 'photos', 'rio', 'lb', 'sas', 'xn--fiq64b', 'work', 'song', 'pictet', 'xn--80ao21a', 'blackfriday', 'zuerich', 'pg', 'today', 'vig', 'guitars', 'helsinki', 'dnp', 'android', 'lr', 'com', 'tui', 'no', 'imdb', 'tab', 'walmart', 'xn--mgba7c0bbn0a', 'statebank', 'science', 'link', 'cg', 'fedex', 'wow', 'fitness', 'ly', 'group', 'us', 'ikano', 'dvag', 'volvo', 'gallo', 'srl', 'marriott', 'ntt', 'ki', 'xn--mgba3a3ejt', 'xn--55qw42g', 'merckmsd', 'club', 'hisamitsu', 'llp', 'amsterdam', 'trust', 'ga', 'systems', 'alibaba', 'xn--3pxu8k', 'xn--mgbayh7gpa', 'bid', 'jpmorgan', 'xn--kput3i', 'taobao', 'cruise', 'party', 'qpon', 'solutions', 'lifeinsurance', 'care', 'ng', 'crown', 'lamborghini', 'xn--h2brj9c8c', 'xn--ngbc5azd', 'py', 'hn', 'tk', 'panasonic', 'saarland', 'london', 'kerryhotels', 'teva', 'navy', 'gives', 'td', 'capitalone', 'house', 'vivo', 'gg', 'gmail', 'xn--mk1bu44c', 'chintai', 'rich', 'ubs', 'mm', 'futbol', 'mv', 'nl', 'xerox', 'bcg', 'markets', 'xn--90ae', 'studio', 'hdfc', 'gs', 'games', 'wed', 'aco', 'so', 'safe', 'sr', 'aws', 'vin', 'hsbc', 'ma', 'norton', 'biz', 'gent', 'tf', 'insure', 'cern', 'gb', 'top', 'living', 'homegoods', 'pictures', 'bofa', 'fresenius', 'lidl', 'directory', 'degree', 'pink', 'lpl', 'mu', 'xn--wgbh1c', 'fj', 'dance', 'training', 'football', 'mtr', 'okinawa', 'band', 'ni', 'mil', 'reliance', 'nhk', 'bms', 'pru', 'pk', 'infiniti', 'seven', 'hangout', 'xn--w4rs40l', 'bloomberg', 'ru', 'cheap', 'ibm', 'zm', 'xn--rvc1e0am3e', 'watches', 'in', 'bw', 'golf', 'auction', 'gop', 'gm', 'now', 'cbre', 'microsoft', 'weatherchannel', 'forex', 'azure', 'pe', 'ericsson', 'xn--b4w605ferd', 'museum', 'study', 'et', 'bv', 'graphics', 'mormon', 'sfr', 'weather', 'madrid', 'ltda', 'nu', 'brussels', 'moscow', 'dm', 'bs', 'tmall', 'vodka', 'clubmed', 'global', 'lefrak', 'tj', 'gea', 'marketing', 'you', 'ryukyu', 'dtv', 'cbn', 'health', 'xn--fiqs8s', 'hockey', 'moda', 'bmw', 'sohu', 'origins', 'stcgroup', 'deals', 'cam', 'bd', 'mlb', 'computer', 'lincoln', 'datsun', 'shopping', 'cu', 'gle', 'equipment', 'scot', 'xn--d1acj3b', 'swatch', 'zappos', 'xn--90a3ac', 'xn--ogbpf8fl', 'fm', 'wales', 'az', 'mortgage', 'xn--fct429k', 'black', 'bradesco', 'clinic', 'tires', 'radio', 'weibo', 'next', 'fr', 'room', 'fire', 'genting', 'coop', 'xn--clchc0ea0b2g2a9gcd', 'expert', 'tv', 'pid', 'tjx', 'direct', 'melbourne', 'watch', 'build', 'sky', 'one', 'foo', 'jaguar', 'redstone', 'sap', 'nikon', 'yoga', 'abbott', 'cba', 'xn--efvy88h', 'ps', 'at', 'ferrari', 'promo', 'bg', 'reit', 'kaufen', 'lgbt', 'dubai', 'sy', 'xn--nqv7f', 'tokyo', 'jprs', 'lanxess', 'phd', 'fund', 'live', 'ovh', 'sm', 'camera', 'lds', 'xn--y9a3aq', 'seat', 'fast', 'bj', 'ink', 'aquarelle', 'schule', 'boutique', 'mh', 'wme', 'coffee', 'country', 'toray', 'xn--80adxhks', 'gmbh', 'spot', 'cricket', 'wang', 'sakura', 'xn--kpry57d', 'xn--mgbab2bd', 'shouji', 'komatsu', 'info', 'bn', 'boo', 'alsace', 'xn--30rr7y', 'pay', 'property', 'total', 'autos', 'ups', 'bing', 'pfizer', 'express', 'pizza', 'cuisinella', 'fashion', 'weir', 'maif', 'repair', 'reviews', 'bcn', 'holdings', 'xn--bck1b9a5dre4c', 'rwe', 'final', 'ong', 'builders', 'kosher', 'star', 'kia', 'lv', 'icbc'}
tlds = list(tlds)
tlds.sort(reverse=True, key=len)

proxies = ["self"]
# count = 0
with open('/home/deus/documents/proxies.txt') as proxy_file:
    for proxy in proxy_file:
        proxy = proxy.replace("\n","")
        if proxy != "":
            proxy = proxy.split(':')
            proxies.append(proxy[1])
            # count += 1
            # if count == 20:
            #     break

manager = multiprocessing.Manager()
used_proxies_across_processes = manager.list()
used_config_files_for_censys_across_processes = manager.list()
used_config_files_for_chaos_across_processes = manager.list()
used_config_files_for_securitytrails_across_processes = manager.list()
exhausted_config_files_for_securitytrails = manager.list()
exhausted_config_files_for_censys = manager.list()
counter = multiprocessing.Value('i',1)
domains_len = 0

config_files = list()
for f_or_d in os.listdir('/home/deus/documents'):
    if "provider-config" in f_or_d:
        config_files.append(f_or_d)


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

def domains_list_generate(assets):
    domains_to_be_used = list()
    for asset in assets:
        if valid_domain(asset):
            domains_to_be_used.append(asset)
        elif valid_subdomain(asset):
            domains_to_be_used.append(get_domain_from_subdomain(asset))

    return domains_to_be_used

# domains_list_generate(asset_list_prepare())

#subfinder -dL domains_to_be_used -all -stats > subfinder_output.txt && cat subfinder_output.txt | anew ./collected_domains.txt && grep -q $domain /home/deus/lists/results.txt; [ $? -eq 0 ] && cat /home/deus/lists/results.txt | anew ./collected_domains.txt ; [ -f "./domains" ] && massdns <(comm <( cat ./collected_domains.txt | sort -u) <(cat ./domains.txt | sort -u) -3) -t A -r /home/deus/documents/resolvers-trusted.txt --retry REFUSED --retry FORMERR --retry SERVFAIL -i 10000 -s 500 -o S > ./resolved_domains.txt || massdns ./collected_domains.txt -t A -r /home/deus/documents/resolvers-trusted.txt --retry REFUSED --retry FORMERR --retry SERVFAIL -i 10000 -s 500 -o S > ./resolved_domains.txt ; cat ./resolved_domains.txt | cut -d \  -f1 | sed s/.$// | sort -u | anew ./domains.txt

domains = list(set(domains_list_generate(asset_list_prepare())))
domains_to_be_deleted_from_domains_list_set = manager.list()

def collect_domains_to_be_removed(domain_or_subdomain):
    global domains
    global domains_to_be_deleted_from_domains_list_set
    performed_subdomain_enum_before_on_this_domain = False
    for domain in domains:
        if domain in domain_or_subdomain:
            domains_to_be_deleted_from_domains_list_set.append(domains.index(domain))
            break

domains_to_be_removed = list()
if os.path.exists('collected_domains.txt'):
    with open('collected_domains.txt') as collected_domains_list:
        for domain in collected_domains_list:
            domain = domain.replace("\n","")
            domains_to_be_removed.append(domain)

pool = multiprocessing.Pool(4)
pool.map(collect_domains_to_be_removed, domains_to_be_removed, chunksize=1)

domains_to_be_deleted_from_domains_list_set = set(domains_to_be_deleted_from_domains_list_set)
new_domains_list = list()
for i in range(0, len(domains)):
    if i not in domains_to_be_deleted_from_domains_list_set:
        new_domains_list.append(domains[i])

domains = new_domains_list
def collect_subdomains(domain):

    global used_proxies_across_processes
    global proxies
    global domains
    global config_files
    global used_config_files_for_censys_across_processes
    global used_config_files_for_chaos_across_processes
    global used_config_files_for_securitytrails_across_processes
    global exhausted_config_files_for_securitytrails
    global exhausted_config_files_for_censys
    
    while True:
        try:
            proxy = list(set(proxies) - set(used_proxies_across_processes))[0]
            used_proxies_across_processes.append(proxy)
            break
        except:
            time.sleep(2)

    condition_of_waybackarchive_subfinder_output = ""
    condition_of_securitytrails_subfinder_output = ""
    condition_of_censys_subfinder_output = ""
    condition_of_chaos_subfinder_output = ""
    def filter_file(file_path, domain_to_check):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        filtered_lines = [line for line in lines if domain_to_check in line]

        with open(file_path, 'w') as file:
            file.writelines(filtered_lines)
    
    index_of_domain = domains.index(domain)
    
    # if proxy == "self":
    #     time.sleep(10)
    # else:
    #     time.sleep(9)
    
    # for proxy in unused_proxies:
    if proxy == "self":
        subprocess.run(f'/bin/bash -c \'subfinder -d {domain} -all -es crtsh,sitedossier -stats -o subfinder_output_{index_of_domain}.txt &> all_subfinder_output_{index_of_domain}.txt \' ', shell=True)
    else:
        subprocess.run(f'/bin/bash -c \'subfinder -d {domain} -all -es crtsh,sitedossier -stats -o subfinder_output_{index_of_domain}.txt -proxy socks5h://isp.smartproxy.com:{proxy} &> all_subfinder_output_{index_of_domain}.txt \' ', shell=True)
    
    # subprocess.run(f"cat subfinder_output_{index_of_domain}.txt | anew ./collected_domains.txt",shell=True)
    subprocess.run(f'/bin/bash -c \'cat all_subfinder_output_{index_of_domain}.txt >> logfile.log \' ', shell=True)

    command_for_waybackarchive = "grep wayback all_subfinder_output_replaceme.txt | awk \'{ print $4}\' ".replace("replaceme",str(index_of_domain))
    command_for_securitytrails = "grep securitytrails all_subfinder_output_replaceme.txt | awk \'{ print $4}\' ".replace("replaceme",str(index_of_domain))
    command_for_censys = "grep censys all_subfinder_output_replaceme.txt | awk \'{ print $4}\' ".replace("replaceme",str(index_of_domain))
    command_for_chaos = "grep chaos all_subfinder_output_replaceme.txt | awk \'{ print $4}\' ".replace("replaceme",str(index_of_domain))
    # command_for_crtsh = "grep crtsh all_subfinder_output_replaceme.txt | awk \'{ print $4}\' ".replace("replaceme",str(index_of_domain))

    condition_of_waybackarchive_subfinder_output = subprocess.run(command_for_waybackarchive, shell=True, capture_output=True, text=True).stdout
    condition_of_securitytrails_subfinder_output = subprocess.run(command_for_securitytrails, shell=True, capture_output=True, text=True).stdout
    condition_of_censys_subfinder_output = subprocess.run(command_for_censys, shell=True, capture_output=True, text=True).stdout
    condition_of_chaos_subfinder_output = subprocess.run(command_for_chaos, shell=True, capture_output=True, text=True).stdout
    # condition_of_crtsh_subfinder_output = subprocess.run(command_for_crtsh, shell=True, capture_output=True, text=True).stdout
    # break

    filter_file(f"subfinder_output_{index_of_domain}.txt", domain)
    
    # if "1" in condition_of_securitytrails_subfinder_output:
    #     used_configs_in_this_process = list()
    #     failure_count = 0

    #     if len(exhausted_config_files_for_securitytrails) != len(config_files):
    #         for i in range(0, 4):
    #             if len(exhausted_config_files_for_securitytrails) != len(config_files):
    #                 # proxy = list(set(proxies) - set(used_proxies_across_processes))[0]

    #                 # for i in range(0,min(len(unused_proxies),len(config_files))):
    #                 #     config_file = config_files[i]
    #                 #     proxy = unused_proxies[i]
    #                 #     used_proxies_across_processes.append(proxy)

    #                 config_file = list(set(config_files) - set(used_config_files_for_securitytrails_across_processes).union(set(used_configs_in_this_process).union(set(exhausted_config_files_for_securitytrails))))[0]
    #                 used_config_files_for_securitytrails_across_processes.append(config_file)
    #                 used_configs_in_this_process.append(config_file)

    #                 # for config_file in config_files:
    #                 if proxy == "self":
    #                     subprocess.run(f'/bin/bash -c \'subfinder -d {domain} -s securitytrails -pc /home/deus/documents/{config_file} -stats -v -o subfinder_output_{index_of_domain}.txt &> all_subfinder_output_{index_of_domain}.txt \' ', shell=True)
    #                 else:
    #                     subprocess.run(f'/bin/bash -c \'mgraftcp --socks5 "{proxy}" --socks5_username "seudxs" --socks5_password "Nz7ZC7jZY54YfmG6Fc8a" subfinder -d {domain} -s securitytrails -pc /home/deus/documents/{config_file} -stats -v -o subfinder_output_{index_of_domain}.txt &> all_subfinder_output_{index_of_domain}.txt \' ', shell=True)

    #                 subprocess.run(f'/bin/bash -c \'cat all_subfinder_output_{index_of_domain}.txt >> logfile.log \' ', shell=True)
    #                 command = "grep securitytrails all_subfinder_output_replaceme.txt | awk \'{ print $4}\'".replace("replaceme",str(index_of_domain))
    #                 condition_of_subfinder_output = subprocess.run(command, shell=True, capture_output=True, text=True).stdout
    #                 if "0" in condition_of_subfinder_output:
    #                     subprocess.run(f'/bin/bash -c \' cat subfinder_output_{index_of_domain}.txt | anew ./collected_domains.txt \' ', shell=True)
    #                     break
                    
    #                 condition_of_subfinder_output = subprocess.run(f"cat all_subfinder_output_{index_of_domain}.txt", shell=True, capture_output=True, text=True).stdout
    #                 if "You've exceeded the usage limits for your account" in condition_of_subfinder_output:
    #                     exhausted_config_files_for_securitytrails.append(config_file)
    #                 failure_count += 1
    #                 error_count_file = open("error_count", "a")
    #                 error_count_file.write(str(failure_count) + "\n")
    #                 error_count_file.close()

    #                 used_config_files_for_securitytrails_across_processes.remove(config_file)

    # if "1" in condition_of_censys_subfinder_output:
    #     used_configs_in_this_process = list()
    #     failure_count = 0

    #     if len(exhausted_config_files_for_censys) != len(config_files):
    #         for i in range(0, 4):
    #             if len(exhausted_config_files_for_censys) != len(config_files):
    #                 # proxy = list(set(proxies) - set(used_proxies_across_processes))[0]
    
    #                 # for i in range(0,min(len(unused_proxies),len(config_files))):
    #                 #     config_file = config_files[i]
    #                 #     proxy = unused_proxies[i]
    #                 #     used_proxies_across_processes.append(proxy)
    
    #                 config_file = list(set(config_files) - set(used_config_files_for_censys_across_processes).union(set(used_configs_in_this_process).union(set(exhausted_config_files_for_censys))))[0]
    #                 used_config_files_for_censys_across_processes.append(config_file)
    #                 used_configs_in_this_process.append(config_file)
    
    #                 # for config_file in config_files:
    #                 if proxy == "self":
    #                     subprocess.run(f'/bin/bash -c \'subfinder -d {domain} -s censys -pc /home/deus/documents/{config_file} -stats -v -o subfinder_output_{index_of_domain}.txt &> all_subfinder_output_{index_of_domain}.txt \' ', shell=True)
    #                 else:
    #                     subprocess.run(f'/bin/bash -c \'mgraftcp --socks5 "{proxy}" --socks5_username "seudxs" --socks5_password "Nz7ZC7jZY54YfmG6Fc8a" subfinder -d {domain} -s censys -pc /home/deus/documents/{config_file} -stats -v -o subfinder_output_{index_of_domain}.txt &> all_subfinder_output_{index_of_domain}.txt \' ', shell=True)
    
    #                 subprocess.run(f'/bin/bash -c \'cat all_subfinder_output_{index_of_domain}.txt >> logfile.log \' ', shell=True)
    
    #                 command = "grep censys all_subfinder_output_replaceme.txt | awk \'{ print $4}\'".replace("replaceme",str(index_of_domain))
    #                 condition_of_subfinder_output = subprocess.run(command, shell=True, capture_output=True, text=True).stdout
    #                 if "0" in condition_of_subfinder_output:
    #                     subprocess.run(f'/bin/bash -c \' cat subfinder_output_{index_of_domain}.txt | anew ./collected_domains.txt \' ', shell=True)
    #                     break

    #                 condition_of_subfinder_output = subprocess.run(f"cat all_subfinder_output_{index_of_domain}.txt", shell=True, capture_output=True, text=True).stdout
    #                 if "Access was denied for this resource or feature" in condition_of_subfinder_output:
    #                     exhausted_config_files_for_censys.append(config_file)
    #                 failure_count += 1
    #                 error_count_file = open("error_count", "a")
    #                 error_count_file.write(str(failure_count) + "\n")
    #                 error_count_file.close()
    
    #                 used_config_files_for_censys_across_processes.remove(config_file)


    if "1" in condition_of_chaos_subfinder_output:
        
        # used_configs_in_this_process = list()
        failure_count = 0
        while True:
            # proxy = list(set(proxies) - set(used_proxies_across_processes))[0]

            # for i in range(0,min(len(unused_proxies),len(config_files))):
            #     config_file = config_files[i]
            #     proxy = unused_proxies[i]
            #     used_proxies_across_processes.append(proxy)

            # config_file = list(set(config_files) - set(used_config_files_for_chaos_across_processes))[0]
            # used_config_files_for_chaos_across_processes.append(config_file)
            # used_configs_in_this_process.append(config_file)

            config_file = config_files[proxies.index(proxy)]

            # for config_file in config_files:
            if proxy == "self":
                subprocess.run(f'/bin/bash -c \'subfinder -d {domain} -s chaos -pc /home/deus/documents/{config_file} -stats -o subfinder_output_{index_of_domain}_chaos.txt &> all_subfinder_output_{index_of_domain}.txt \' ', shell=True)
            else:
                subprocess.run(f'/bin/bash -c \'subfinder -d {domain} -s chaos -pc /home/deus/documents/{config_file} -stats -o subfinder_output_{index_of_domain}_chaos.txt -proxy socks5h://isp.smartproxy.com:{proxy} &> all_subfinder_output_{index_of_domain}.txt \' ', shell=True)
            
            subprocess.run(f'/bin/bash -c \'cat all_subfinder_output_{index_of_domain}.txt >> logfile.log \' ', shell=True)
            
            command = "grep chaos all_subfinder_output_replaceme.txt | awk \'{ print $4}\'".replace("replaceme",str(index_of_domain))
            condition_of_subfinder_output = subprocess.run(command, shell=True, capture_output=True, text=True).stdout
            if "0" in condition_of_subfinder_output:
                # subprocess.run(f'/bin/bash -c \' cat subfinder_output_{index_of_domain}.txt | anew ./collected_domains.txt \' ', shell=True)
                break
            if failure_count > 15:
                break
            if failure_count % 5 == 0:
                time.sleep(60)
            failure_count += 1
            error_count_file = open("error_count", "a")
            error_count_file.write(str(failure_count) + "\n")
            error_count_file.close()

        filter_file(f"subfinder_output_{index_of_domain}_chaos.txt", domain)

    # if "1" in condition_of_crtsh_subfinder_output:
        
    #     failure_count = 0
    #     while True:


    #         if proxy == "self":
    #             subprocess.run(f'/bin/bash -c \'subfinder -d {domain} -s crtsh -stats -o subfinder_output_{index_of_domain}_crtsh.txt &> all_subfinder_output_{index_of_domain}.txt \' ', shell=True)
    #         else:
    #             subprocess.run(f'/bin/bash -c \'subfinder -d {domain} -s crtsh -stats -o subfinder_output_{index_of_domain}_crtsh.txt -proxy socks5h://isp.smartproxy.com:{proxy} &> all_subfinder_output_{index_of_domain}.txt \' ', shell=True)
            
    #         subprocess.run(f'/bin/bash -c \'cat all_subfinder_output_{index_of_domain}.txt >> logfile.log \' ', shell=True)
            
    #         command = "grep crtsh all_subfinder_output_replaceme.txt | awk \'{ print $4}\'".replace("replaceme",str(index_of_domain))
    #         condition_of_subfinder_output = subprocess.run(command, shell=True, capture_output=True, text=True).stdout
    #         if "0" in condition_of_subfinder_output:
    #             break
    #         if failure_count > 15:
    #             break
    #         if failure_count % 5 == 0:
    #             time.sleep(60)
    #         failure_count += 1
    #         error_count_file = open("error_count", "a")
    #         error_count_file.write(str(failure_count) + "\n")
    #         error_count_file.close()

    #     filter_file(f"subfinder_output_{index_of_domain}_crtsh.txt", domain)

    # if proxy == "self":
    #     time.sleep(10)
    # else:
    #     time.sleep(9)
    
    if "1" in condition_of_waybackarchive_subfinder_output:
        failure_count = 0
        while True:
            if proxy == "self":
                subprocess.run(f'/bin/bash -c \'subfinder -d {domain} -s waybackarchive -stats -o subfinder_output_{index_of_domain}_waybackarchive.txt &> all_subfinder_output_{index_of_domain}.txt \' ', shell=True)
            else:
                subprocess.run(f'/bin/bash -c \'subfinder -d {domain} -s waybackarchive -stats -o subfinder_output_{index_of_domain}_waybackarchive.txt -proxy socks5h://isp.smartproxy.com:{proxy} &> all_subfinder_output_{index_of_domain}.txt \' ', shell=True)
            
            subprocess.run(f'/bin/bash -c \'cat all_subfinder_output_{index_of_domain}.txt >> logfile.log \' ', shell=True)

            command = "grep wayback all_subfinder_output_replaceme.txt | awk \'{ print $4}\' ".replace("replaceme",str(index_of_domain))
            condition_of_subfinder_output = subprocess.run(command, shell=True, capture_output=True, text=True).stdout
            if "0" in condition_of_subfinder_output:
                # subprocess.run(f'/bin/bash -c \' cat subfinder_output_{index_of_domain}.txt | anew ./collected_domains.txt \' ', shell=True)
                break
            if failure_count > 15:
                break
            if failure_count % 5 == 0:
                time.sleep(60)
            failure_count += 1
            error_count_file = open("error_count", "a")
            error_count_file.write(str(failure_count) + "\n")
            error_count_file.close()

        filter_file(f"subfinder_output_{index_of_domain}_waybackarchive.txt", domain)

    used_proxies_across_processes.remove(proxy)
    subprocess.run(f'/bin/bash -c \'rm all_subfinder_output_{index_of_domain}.txt \' ', shell=True)

    global counter
    global domains_len
    log_file = open("logfile.log", "a")
    log_file.write("Finished " + str(counter.value) + "/" + str(domains_len) + "\n")
    log_file.close()
    with counter.get_lock():
        counter.value += 1

domains_len = len(domains)

pool = multiprocessing.Pool(20)
pool.map(collect_subdomains, domains, chunksize=1)

def output_collected_domains_file(input_files, output_file):
    unique_lines = set()
    for file_name in input_files:
        with open(file_name, 'r') as file:
            for line in file:
                unique_lines.add(line.replace("\n",""))

    with open(output_file, 'a') as output:
        for line in unique_lines:
            output.write(line + '\n')
    
    for file_name in input_files:
        os.remove(file_name)

input_files = list()
for f_or_d in os.listdir('./'):
    if "subfinder_output_" in f_or_d:
        input_files.append(f_or_d)

output_file = 'collected_domains.txt'
output_collected_domains_file(input_files, output_file)


# subprocess.run(f"cat subfinder_output_*.txt | anew ./collected_domains.txt",shell=True)
# subprocess.run(f'/bin/bash -c \'rm subfinder_output_*.txt \' ', shell=True)

# unresolved_domains = set()
# if os.path.exists('domains.txt'):
#     resolved_domains = set()
    
#     with open('domains.txt') as domains_list:
#         for domain in domains_list:
#             domain = domain.replace("\n","")
#             resolved_domains.add(domain)
#     with open('collected_domains.txt') as collected_domains_list:
#         for domain in collected_domains_list:
#             domain = domain.replace("\n","")
#             unresolved_domains.add(domain)
#     unresolved_domains = list(unresolved_domains - resolved_domains)
# else:
#     with open('collected_domains.txt') as collected_domains_list:
#         for domain in collected_domains_list:
#             domain = domain.replace("\n","")
#             unresolved_domains.add(domain)
#     unresolved_domains = list(unresolved_domains)

# def divide_chunks(l, n): 
#     for i in range(0, len(l), n):  
#         yield l[i:i + n]

# divided_collected_domains = list(divide_chunks(unresolved_domains,math.ceil(len(unresolved_domains) / 3)))

# for i in range(0, len(divided_collected_domains)):
#     with open(f'collected_domains_{i}.txt','w') as file:
#         for unresolved_domain in divided_collected_domains[i]:
#             file.write(unresolved_domain + "\n")

# def resolve_domains(file_id):
#     global proxies
#     global used_proxies_across_processes

#     proxy = list(set(proxies) - set(used_proxies_across_processes))[0]
#     used_proxies_across_processes.append(proxy)
#     # index_of_domain = domains.index(domain)

#     if proxy == "self":
#         subprocess.run(f'/bin/bash -c \'massdns ./collected_domains_{file_id}.txt -t A -r /home/deus/documents/resolvers-trusted.txt --retry REFUSED --retry FORMERR --retry SERVFAIL -i 10000 -s 500 -o S > ./resolved_domains_{file_id}.txt \' ', shell=True)
#     else:
#         while True:
#             try:
#                 subprocess.run(f'/bin/bash -c \' proxychains4 -f /home/deus/documents/{proxy} -q massdns ./collected_domains_{file_id}.txt -t A -r /home/deus/documents/resolvers-trusted.txt --retry REFUSED --retry FORMERR --retry SERVFAIL -i 10000 -s 500 -o S > ./resolved_domains_{file_id}.txt \' ', shell=True, timeout=10800)
#                 break
#             except subprocess.TimeoutExpired:
#                 continue
    
#     used_proxies_across_processes.remove(proxy)

# proxies = ["self"]
# for f_or_d in os.listdir('/home/deus/documents'):
#     if "proxychains" in f_or_d:
#         proxies.append(f_or_d)

# p1 = multiprocessing.Process(target=resolve_domains,args=('0',))
# p2 = multiprocessing.Process(target=resolve_domains,args=('1',))
# p3 = multiprocessing.Process(target=resolve_domains,args=('2',))

# p1.start()
# p2.start()
# p3.start()

# p1.join()
# p2.join()
# p3.join()

subprocess.run(f'/bin/bash -c \'massdns ./collected_domains.txt -t A -r /home/deus/documents/resolvers-trusted.txt --retry REFUSED --retry FORMERR --retry SERVFAIL -o S > ./resolved_domains.txt \' ', shell=True)
subprocess.run(f'/bin/bash -c \'cat ./resolved_domains.txt | cut -d \  -f1 | sed "s/.$//" | sort -u | anew ./domains.txt \' ', shell=True)
# subprocess.run(f'/bin/bash -c \'rm collected_domains_0.txt collected_domains_1.txt collected_domains_2.txt resolved_domains_0.txt resolved_domains_1.txt resolved_domains_2.txt \' ', shell=True)