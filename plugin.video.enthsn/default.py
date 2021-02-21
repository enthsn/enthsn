# einthusan.com plugin written by humla.
# einthusan.com Plugin maintained by ReasonsRepo
# einthusan.com Plugin maintained by ssreekanth

import base64
from datetime import date
import html
import html2text
import json
import os
import re
import requests
from urllib.parse import urlparse, quote_plus, unquote_plus
from kodi_six import xbmc, xbmcplugin, xbmcgui, xbmcaddon

import HTTPInterface
import JSONInterface
import DBInterface

# Get the plugin url in plugin:// notation.
_plugin_url = sys.argv[0]
# Get the plugin handle as an integer number.
_plugin_handle = int(sys.argv[1])

NUMBER_OF_PAGES = 3
ADDON = xbmcaddon.Addon(id='plugin.video.enthsn')

username = ADDON.getSetting('enthsn.username')
password = ADDON.getSetting('enthsn.password')

locationStr = xbmcplugin.getSetting(_plugin_handle, 'enthsn.location')
Locations = ['Los Angeles', 'Dallas', 'Washington D.C', 'London', 'No Preference']
locationId = int(locationStr)
if (locationId > len(Locations) - 1):
    locationId = len(Locations) - 1
location = Locations[locationId]

videoQualityStr = xbmcplugin.getSetting(_plugin_handle, 'enthsn.video.quality')
VideoQualityOptions = ['SD/HD', 'UHD']
videoQualityId = int(videoQualityStr)
if (videoQualityId > len(VideoQualityOptions) -1):
    videoQualityId = 0
videoQuality = VideoQualityOptions[videoQualityId]


EINTHUSAN_URL='https://www.einthusan.tv'

einthusanRedirectUrl = '';

cwd = ADDON.getAddonInfo('path')
img_path = cwd + '/images/'

##
# Prints the main categories. Called when id is 0.
##
def main_categories(name, url, language, mode):
    global einthusanRedirectUrl
    languages = []
    try:
        r = requests.get(EINTHUSAN_URL)

        if einthusanRedirectUrl == '':
            parsedUrl=urlparse(r.url);
            einthusanRedirectUrl='{uri.scheme}://{uri.netloc}'.format(uri=parsedUrl)
            xbmc.log('Einthusan Redirect URL: '+einthusanRedirectUrl, level=xbmc.LOGINFO)
        
        matches = re.findall('<li><a href=".*?\?lang=(.+?)"><div.*?div><img src="(.+?)"><p class=".*?-bg">(.+?)<\/p>',
                             r.text)
        if len(matches) != 0:
            languages = matches
            
    except:
        xbmcgui.Dialog().ok("Network Error",
                            "Please check your network connectivity",
                            "Try restarting the addon")
        return


    xbmcplugin.setContent(_plugin_handle, 'videos')
    for lang_item in languages:
        lang = str(lang_item[0])
        title = str(lang_item[2])
        if "http" not in lang_item[1] and lang_item[1] != "":
            image = "https://" + str(lang_item[1])
        else:
            image = ""
        addDir(title, '', 7, image, lang, title+' movies', image)
    addDir('Addon Settings', '', 12, 'DefaultAddonService.png',  '',          'Settings')
    xbmcplugin.endOfDirectory(_plugin_handle)

##
# Shows categories for each language
##
def inner_categories(name, url, language, mode):
    xbmcplugin.setContent(_plugin_handle, 'videos')
    postData = 'lang=' + language
    addDir('Featured',      '',       4,  'DefaultAddonsRecentlyUpdated.png', language, 'Featured Movies')
    addDir('Recent',        postData, 3,  'DefaultRecentlyAddedMovies.png', language, 'Recently Added Movies')
    addDir('Staff Picks',   postData, 5,  'DefaultMovies.png', language, 'Movies picked by Staff')
    addDir('A-Z',           postData, 8,  'DefaultMovieTitle.png', language, 'Browse movies sorted alphabetically')
    addDir('Years',         postData, 9,  'DefaultYear.png', language, 'Browse movies sorted by release year')
    #addDir('Cast',          postData, 10, '', language, 'Browse movies by Cast')
    #addDir('Director',      postData, 10, '', language, 'Browse movies by Director')
    addDir('Search',        postData, 6,  'DefaultAddonsSearch.png', language, 'Search for movies')
    xbmcplugin.endOfDirectory(_plugin_handle)

##
#  Scrapes a list of movies and music videos from the website. Called when mode is 1.
##
def get_movies_and_music_videos(name, url, language, mode):
    get_movies_and_music_videos_helper(name, url, language, page=1)

def get_movies_and_music_videos_helper(name, url, language, page):
    # xbmc.log(url, level=xbmc.LOGINFO)
    #xbmcplugin.setPluginCategory(_plugin_handle, name)
    xbmcplugin.setContent(_plugin_handle, 'movies')
    referurl = url
    htmlcontent =  requests.get(url).text
    matches = re.compile('<div class="block1">.*?href=".*?watch\/(.*?)\/\?lang=(.*?)".*?<img src="(.+?)".+?<h3>(.+?)<\/h3>.+?<p>(.+?)<span>(.+?)<\/span>.+?i class=(.+?)<p class=".*?synopsis">\s*(.+?)\s*<\/p><div class="professionals">(.*?)<\/div><\/div><div class="block3">.+?<span>Wiki<\/span>.+?<a(.+?)Trailer<\/span>').findall(htmlcontent)
    for id, lang, img, name, year, genre, ishd, synopsis, prof_content, trailer_content in matches:
        name = str(name.replace(",","").encode('ascii', 'ignore').decode('ascii'))
        movie = str(name)+','+str(id)+','+lang+','
        if 'ultrahd' in ishd:
            movie = movie+'itshd,'+referurl
        else:
            movie = movie+'itsnothd,'+referurl
        image = 'https:' + img
        try:
            description = synopsis.encode('ascii', 'ignore').decode('ascii')
        except:
            description=""

        info = {
            'plot': html.unescape(html2text.html2text(description).replace('\n', ' ').replace('\r', '')),
            'genre': genre,
            'year': year,
            'title': html2text.html2text(name),
            'originaltitle': html2text.html2text(name),
            'mediatype': 'movie',
            'country': 'India',
            'cast': [],
            'director': [],
            'artist': []
        }

        prof_matches = re.compile('<input.+?<img src="(.+?)">.+?<p>(.+?)<\/p><label>(.+?)<\/label>').findall(prof_content)
        for prof_img, prof_name, prof_label in prof_matches:
            if (prof_label == 'Director'):
                info['director'].append(prof_name)
            else:
                info['cast'].append((prof_name, prof_label))

        try:
            trailer_link = re.search('href="(.+?)"', trailer_content)
            if trailer_link:
                trailer_id = re.findall('^[^v]+v=(.{3,11}).*', trailer_link.group(0))[0]
                info['trailer'] = 'plugin://plugin.video.youtube/play/?video_id=%s' % trailer_id
        except:
            pass

        addStream(name, movie, 2, image, lang, info)

    nextpage=re.findall('data-disabled="([^"]*)" href="(.+?)"', htmlcontent)[-1]
    if nextpage[0]!='true':
        nextPage_Url = einthusanRedirectUrl+nextpage[1]
        if (page >= NUMBER_OF_PAGES):
            addDir('[I]Next Page[/I]', nextPage_Url, 1, 'DefaultFolder.png', '', 'Shows the next page of movies...')
        else:
            get_movies_and_music_videos_helper(name, nextPage_Url, language, page+1)

    xbmcplugin.endOfDirectory(_plugin_handle)
    # s.close()

# Shows the movie in the homepage..
def show_featured_movies(name, url, language, mode):
    page_url = einthusanRedirectUrl+'/movie/browse/?lang=' + language

    xbmcplugin.setContent(_plugin_handle, 'movies')
    # xbmc.log(page_url, level=xbmc.LOGINFO)
    htmlcontent = requests.get(page_url).text
    matches = re.compile('name="newrelease_tab".+?img src="(.+?)".+?href="\/movie\/watch\/(.+?)\/\?lang=(.+?)"><h2>(.+?)<\/h2>.+?<p>(.+?)<span>(.+?)<\/span>.+?i class=(.+?)<\/div>.+?<span>Wiki<\/span>.+?<a(.+?)>Trailer<\/span>.+?<div class="professionals">(.*?)<\/div><\/div>( <input type="radio" id="_newrelease|<ul class=)').findall(htmlcontent)

    for img, id, lang, name, year, genre, ishd, trailer_content, prof_content, xyz in matches:
        name = name.replace(",","").encode('ascii', 'ignore').decode('ascii')
        movie = name+','+id+','+lang
        if 'ultrahd' in ishd:
            movie = movie+',itshd,'+page_url
        else:
            movie = movie+',itsnothd,'+page_url
        image = 'https:' + img

        movie_url=einthusanRedirectUrl+'/movie/watch/%s/?lang=%s'%(id,lang)
        movie_html = requests.get(movie_url).text
        synopsis = re.findall('<p class=".*?synopsis">\s*(.+?)\s*<\/p>', movie_html)
        if synopsis:
            description = synopsis[0].encode('ascii', 'ignore').decode('ascii')
        else:
            description = ''

        info = {
            'plot': html.unescape(html2text.html2text(description).replace('\n', ' ').replace('\r', '')),
            'genre': genre,
            'year': year,
            'title': html2text.html2text(name),
            'originaltitle': html2text.html2text(name),
            'mediatype': 'movie',
            'country': 'India',
            'cast': [],
            'director': [],
            'artist': []
        }

        prof_matches = re.compile('<input.+?<img src="(.+?)">.+?<p>(.+?)<\/p><label>(.+?)<\/label>').findall(prof_content)
        for prof_img, prof_name, prof_label in prof_matches:
            if (prof_label == 'Director'):
                info['director'].append(prof_name)
            else:
                info['cast'].append((prof_name, prof_label))

        try:
            trailer_link = re.search('href="(.+?)"', trailer_content)
            if trailer_link:
                trailer_id = re.findall('^[^v]+v=(.{3,11}).*', trailer_link.group(0))[0]
                info['trailer'] = 'plugin://plugin.video.youtube/play/?video_id=%s' % trailer_id
        except:
            pass

        addStream(name, movie, 2, image, language, info)

    xbmcplugin.endOfDirectory(_plugin_handle)
    # s.close()

##
#  Just displays three recent sections. Called when id is 3.
##
def show_recent_sections(name, url, language, mode):
    postData = einthusanRedirectUrl+'/movie/results/?'+url+'&find=Recent'
    get_movies_and_music_videos(name, postData, language, mode)

##
# Displays staff picks . Called when id is 5.
##
def show_staff_picks(name, url, language, mode):
    postData = einthusanRedirectUrl+'/movie/results/?'+url+'&find=StaffPick'
    get_movies_and_music_videos(name, postData, language, mode)

##
# Displays the options for A-Z view. Called when id is 8.
##
def show_A_Z(name, url, language, mode):
    xbmcplugin.setContent(_plugin_handle, 'videos')
    azlist = map (chr, range(65,91))
    addDir('Numerical', einthusanRedirectUrl+'/movie/results/?find=Numbers&'+url, 1, '')
    for letter in azlist:
        addDir(letter, einthusanRedirectUrl+'/movie/results/?alpha='+letter+'&find=Alphabets&'+url, 1, '')
    xbmcplugin.endOfDirectory(_plugin_handle)

##
# Single method that shows the list of years, actors and directors.
# Called when id is 9, 10, 11
# 9 : List of Years
# 10: List of Actors
# 11: List of directors
##
def show_list(name, b_url, language, mode):
    xbmcplugin.setContent(_plugin_handle, 'videos')
    if (mode == 9):
        postData = b_url + '&find=Year&year='
        values = [repr(x) for x in reversed(range(1940, date.today().year + 1))]
    elif (mode == 10):
        postData = b_url + '&organize=Cast'
        values = JSONInterface.get_actor_list(language)
    else:
        postData = b_url + '&organize=Director'
        values = JSONInterface.get_director_list(language)

    # postData = postData + '&filtered='

    for attr_value in values:
        if (attr_value != None):
            addDir(attr_value, einthusanRedirectUrl+'/movie/results/?'+postData + str(attr_value), 1, '')

    xbmcplugin.endOfDirectory(_plugin_handle)

##
# Shows the search box for serching. Shown when the id is 6.
##
def show_search_box(name, url, language, mode):
    xbmcplugin.setContent(_plugin_handle, 'movies')
    keyb = xbmc.Keyboard('', 'Search for Movies')
    keyb.doModal()
    if (keyb.isConfirmed()):
        search_term = quote_plus(keyb.getText())
        if len(search_term) == 0:
            return
        postData = einthusanRedirectUrl+'/movie/results/?'+url+'&query=' + search_term
        headers={'Origin':einthusanRedirectUrl,'Referer':einthusanRedirectUrl+'/movie/browse/?'+url,'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
        htmlcontent = requests.get(postData, headers=headers).text
        matches = re.compile('<div class="block1">.*?href=".*?watch\/(.*?)\/\?lang=(.*?)".*?<img src="(.+?)".+?<h3>(.+?)<\/h3>.+?<p>(.+?)<span>(.+?)<\/span>.+?i class=(.+?)<p class=".*?synopsis">\s*(.+?)\s*<\/p><div class="professionals">(.+?)<\/div><\/div><div class="block3">.+?<span>Wiki<\/span>.+?<a(.+?)Trailer<\/span>').findall(htmlcontent)
        for id, lang, img, name, year, genre, ishd, synopsis, prof_content, trailer_content in matches:
            name = name.replace(",","").encode('ascii', 'ignore').decode('ascii')
            movie = str(name)+','+str(id)+','+lang+','
            if 'ultrahd' in ishd:
                movie = movie+'itshd,'+postData
            else:
                movie = movie+'itsnothd,'+postData
            image = 'https:' + img
            try:
                description = synopsis.encode('ascii', 'ignore').decode('ascii')
            except:
                description=""

            info = {
                'plot': html.unescape(html2text.html2text(description).replace('\n', ' ').replace('\r', '')),
                'genre': genre,
                'year': year,
                'title': html2text.html2text(name),
                'originaltitle': html2text.html2text(name),
                'mediatype': 'movie',
                'country': 'India',
                'cast': [],
                'director': [],
                'artist': []
            }

            prof_matches = re.compile('<input.+?<img src="(.+?)">.+?<p>(.+?)<\/p><label>(.+?)<\/label>').findall(prof_content)
            for prof_img, prof_name, prof_label in prof_matches:
                if (prof_label == 'Director'):
                    info['director'].append(prof_name)
                else:
                    info['cast'].append((prof_name, prof_label))

            try:
                trailer_link = re.search('href="(.+?)"', trailer_content)
                if trailer_link:
                    trailer_id = re.findall('^[^v]+v=(.{3,11}).*', trailer_link.group(0))[0]
                    info['trailer'] = 'plugin://plugin.video.youtube/play/?video_id=%s' % trailer_id
            except:
                pass

            addStream(name, movie, 2, image, lang, info)

        nextpage=re.findall('data-disabled="([^"]*)" href="(.+?)"', htmlcontent)[-1]
        if nextpage[0]!='true':
            nextPage_Url = einthusanRedirectUrl+nextpage[1]
            get_movies_and_music_videos_helper(name, nextPage_Url, language, 2)

        xbmcplugin.endOfDirectory(_plugin_handle, cacheToDisc=True)

def http_request_with_login(url):
    username = xbmcplugin.getSetting(_plugin_handle, 'username')
    password = xbmcplugin.getSetting(_plugin_handle, 'password')
    ADDON_USERDATA_FOLDER = xbmc.translatePath(ADDON.getAddonInfo('profile'))
    COOKIE_FILE = os.path.join(ADDON_USERDATA_FOLDER, 'cookies')

    return HTTPInterface.http_get(url, COOKIE_FILE, username, password)

def decodeEInth(lnk):
    t=10
    r=lnk[0:t]+lnk[-1]+lnk[t+2:-1]
    return r

def encodeEInth(lnk):
    t=10
    r=lnk[0:t]+lnk[-1]+lnk[t+2:-1]
    return r

##
# Plays the video. Called when the id is 2.
##
def play_video(name, url, language, mode):

    s = requests.Session()
    # "Playing: " + name + ", with url:"+ url)

    name,url,lang,isithd,referurl=url.split(',')

    if isithd=='itshd':
            if videoQuality == 'SD/HD':
                # isithd = 'itsnothd'
                mainurl=einthusanRedirectUrl+'/movie/watch/%s/?lang=%s'%(url,lang)
                mainurlajax=einthusanRedirectUrl+'/ajax/movie/watch/%s/?lang=%s'%(url,lang)
                # xbmc.log(mainurlajax, LOGINFO)
                headers={'Origin':einthusanRedirectUrl,'Referer':einthusanRedirectUrl+'/movie/browse/?lang=hindi','User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                get_movie(s, mainurl, mainurlajax, headers)
            if videoQuality == 'UHD':
                # isithd = 'itshd'
                mainurl=einthusanRedirectUrl+'/movie/watch/%s/?lang=%s&uhd=true'%(url,lang)
                mainurlajax=einthusanRedirectUrl+'/ajax/movie/watch/%s/?lang=%s&uhd=true'%(url,lang)
                headers={'Origin':einthusanRedirectUrl,'Referer':einthusanRedirectUrl+'/movie/browse/?lang=hindi','User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
                login_info(s, referurl)
                get_movie(s, mainurl, mainurlajax, headers)
    else:
        mainurl=einthusanRedirectUrl+'/movie/watch/%s/?lang=%s'%(url,lang)
        mainurlajax=einthusanRedirectUrl+'/ajax/movie/watch/%s/?lang=%s'%(url,lang)
        headers={'Origin':einthusanRedirectUrl,'Referer':einthusanRedirectUrl+'/movie/browse/?lang=hindi','User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
        get_movie(s,mainurl,mainurlajax, headers)

    #xbmcplugin.endOfDirectory(_plugin_handle)

def get_movie(s, mainurl, mainurlajax, headers=None):

    check_sorry_message = "Our servers are almost maxed"
    check_go_premium = "Go Premium"

    htm=s.get(mainurl, headers=headers, cookies=s.cookies).text

    if re.search(check_sorry_message, htm):
        xbmcgui.Dialog().ok(
            "Server Error",
            "Sorry. Einthusan servers are almost maxed.",
            "Please try again in 5 - 10 mins or upgrade to a Lifetime Premium account.",
        )
        return False

    if re.search(check_go_premium, htm):
        xbmcgui.Dialog().ok(
            "UltraHD Error",
            "Premium Membership Required for UltraHD Movies.",
            "Please add Premium Membership Login details in Addon Settings.",
        )
        return False

    lnk=re.findall('data-ejpingables=["\'](.*?)["\']',htm)[0]

    r=decodeEInth(lnk)
    jdata='{"EJOutcomes":"%s","NativeHLS":false}'%lnk

    gid=re.findall('data-pageid=["\'](.*?)["\']',htm)[0]

    gid=html.unescape(gid)

    postdata={'xEvent':'UIVideoPlayer.PingOutcome','xJson':jdata,'arcVersion':'3','appVersion':'59','gorilla.csrf.Token':gid}

    rdata=s.post(mainurlajax,headers=headers,data=postdata,cookies=s.cookies).text

    r=json.loads(rdata)["Data"]["EJLinks"]
    xbmc.log(base64.b64decode(str(decodeEInth(r))).decode('ascii'), level=xbmc.LOGINFO)
    lnk=json.loads(base64.b64decode(decodeEInth(r)).decode('ascii'))["HLSLink"]

    lnk = preferred_server(lnk, mainurl)

    xbmc.log(lnk, level=xbmc.LOGINFO)

    urlnew=lnk+('|'+einthusanRedirectUrl+'&Referer=%s&User-Agent=%s'%(mainurl,'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'))
    # listitem = xbmcgui.ListItem( label = str(name), icon = "DefaultVideo.png", thumb = xbmc.getInfoImage( "ListItem.Thumb" ) )
    listitem = xbmcgui.ListItem(label = str(name))

    #listitem.setProperty('IsPlayable', 'true')
    listitem.setPath(urlnew)
    xbmcplugin.setResolvedUrl(_plugin_handle, True, listitem)

    s.close()
    # xbmcplugin.endOfDirectory(_plugin_handle)

def preferred_server(lnk, mainurl):
    xbmc.log(location, level=xbmc.LOGINFO)
    if location != 'No Preference':
        if location == 'Dallas':
            servers = [2]
        elif location == 'Washington D.C':
            servers = [1]
        elif location == 'Los Angeles':
            servers = [3]
        elif location == 'London':
            servers = [4]
        else:
            servers = [1]

        server_n = lnk.split('.einthusan.io')[0].strip('https://cdn')
        SERVER_OFFSET = []
        if int(server_n) > 100:
            SERVER_OFFSET.append(100)
        else:
            SERVER_OFFSET.append(0)
        servers.append(int(server_n) - SERVER_OFFSET[0])
        vidpath = lnk.split('.io/')[1]
        new_headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36', 'Referer':mainurl, 'Origin':einthusanRedirectUrl}
        for i in servers:
                urltry = ("https://cdn" + str(i+SERVER_OFFSET[0]) + ".einthusan.io/" + vidpath)
                isitworking = requests.get(urltry, headers=new_headers).status_code
                xbmc.log(urltry, level=xbmc.LOGINFO)
                xbmc.log(str(isitworking), level=xbmc.LOGINFO)
                if isitworking == 200:
                        lnk = urltry
                        break
    return lnk

def login_info(s, referurl):

    headers={'Origin':einthusanRedirectUrl,'Referer':referurl,'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}

    htm = s.get(einthusanRedirectUrl+'/login/?lang=hindi', headers=headers, allow_redirects=False).content
    csrf=re.findall('data-pageid=["\'](.*?)["\']',htm)[0]
    if '&#43;' in csrf: csrf = csrf.replace('&#43;', '+')

    body = {'xEvent':'Login','xJson':'{"Email":"'+username+'","Password":"'+password+'"}', 'arcVersion':3, 'appVersion':59,'tabID':csrf+'48','gorilla.csrf.Token':csrf}

    headers['X-Requested-With']='XMLHttpRequest'

    headers['Referer']=einthusanRedirectUrl+'/login/?lang=hindi'
    html2= s.post(einthusanRedirectUrl+'/ajax/login/?lang=hindi',headers=headers,cookies=s.cookies, data=body,allow_redirects=False)

    html3=s.get(einthusanRedirectUrl+'/account/?flashmessage=success%3A%3A%3AYou+are+now+logged+in.&lang=hindi', headers=headers, cookies=s.cookies)

    csrf3 = re.findall('data-pageid=["\'](.*?)["\']',html3.text)[0]
    body4 = {'xEvent':'notify','xJson':'{"Alert":"SUCCESS","Heading":"AWESOME!","Line1":"You+are+now+logged+in.","Buttons":[]}', 'arcVersion':3, 'appVersion':59,'tabID':csrf+'48','gorilla.csrf.Token':csrf3}
    html4 = s.post(einthusanRedirectUrl+'/ajax/account/?lang=hindi', headers=headers, cookies=s.cookies, data=body4)

    return s

##
# Displays the setting view. Called when mode is 12
##
def display_setting(name, url, language, mode):
    ADDON.openSettings()

def get_params():
    param=[]
    paramstring=sys.argv[2]
    # xbmc.log(paramstring, level=xbmc.LOGINFO)
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param

def addDir(name, url, mode, icon='', lang='',description='', fanart=''):
    u=_plugin_url+"?url="+quote_plus(url)+"&mode="+str(mode)+"&name="+quote_plus(name)+"&lang="+quote_plus(lang)+"&einthusanRedirectUrl="+quote_plus(einthusanRedirectUrl)

    liz=xbmcgui.ListItem(label=html2text.html2text(name))
    liz.setInfo('video', {'plot': description})

    if icon == '':
        icon = 'DefaultFolder.png'

    if fanart == '':
        fanart = cwd + '/fanart.png'

    liz.setArt({'icon': icon,
                'thumb': icon,
                'fanart': fanart})
    ok=xbmcplugin.addDirectoryItem(handle=_plugin_handle, url=u, listitem=liz, isFolder=True)
    return ok

def addStream(name, url, mode, icon='', lang='',info=None):
    u=_plugin_url+"?url="+quote_plus(url)+"&mode="+str(mode)+"&name="+quote_plus(name)+"&lang="+quote_plus(lang)+"&einthusanRedirectUrl="+quote_plus(einthusanRedirectUrl)

    name,url,lang,isithd,referurl=url.split(',')
    if isithd=='itshd':
        name = name + ' [COLOR blue][I]Ultra HD[/I][/COLOR]'
    # if 'trailer' in info:
    #    name = name + ' [COLOR green][I]Trailer[/I][/COLOR]'
    liz=xbmcgui.ListItem(label=html2text.html2text(name))
    liz.setInfo( type='video', infoLabels=info )

    liz.setArt({'icon': icon,
                'thumb': icon,
                'banner': icon,
                'poster': icon,
                'fanart': icon})
    liz.setProperty('IsPlayable', 'true')
    #liz.setRating('einthusan', 4.3, 10, True)

    if 'trailer' in info:
        # xbmc.log('adding context menu item for playing trailer: '+info['trailer'], xbmc.LOGINFO)
        liz.addContextMenuItems([ ('Play trailer', 'RunPlugin(%s)' % info['trailer'], ) ])

    ok=xbmcplugin.addDirectoryItem(handle=_plugin_handle, url=u, listitem=liz, isFolder=False)
    return ok


##### main #####
params=get_params()
url=''
name=''
mode=0
language=''
description=''

try:
    url=unquote_plus(params["url"])
except:
    pass

try:
    name=unquote_plus(params["name"])
except:
    pass

try:
    mode=int(params["mode"])
except:
    pass

try:
    language=unquote_plus(params["lang"])
except:
    pass

try:
    description=unquote_plus(params["description"])
except:
    pass

try:
    einthusanRedirectUrl=unquote_plus(params["einthusanRedirectUrl"])
except:
    pass

# Modes
# 0: The main Categories Menu. Selection of language
# 1: For scraping the movies from a list of movies in the website
# 2: For playing a video
# 3: The Recent Section
# 4: The top viewed list. like above
# 5: The top rated list. Like above
# 6: Search options
# 7: Sub menu
# 8: A-Z view.
# 9: Yearly view
# 10: Actor view
# 11: Director view
# 12: Show Addon Settings

function_map = {}
function_map[0] = main_categories
function_map[1] = get_movies_and_music_videos
function_map[2] = play_video
function_map[3] = show_recent_sections
function_map[4] = show_featured_movies
function_map[5] = show_staff_picks
function_map[6] = show_search_box
function_map[7] = inner_categories
function_map[8] = show_A_Z
function_map[9] = show_list
function_map[10] = show_list
function_map[11] = show_list
function_map[12] = display_setting

function_map[mode](name, url, language, mode)
