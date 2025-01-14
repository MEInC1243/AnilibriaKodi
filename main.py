import json
import sys
from urllib.parse import urlencode, urljoin, parse_qsl
from urllib.request import urlopen, Request
from urllib.error import URLError
import xbmcgui
import xbmcplugin
import xbmc
import socket

BASE_URL = "http://localhost:3000"

def build_url(query):
    return sys.argv[0] + '?' + urlencode(query)

def get_json_response(endpoint, params=None):
    try:
        url = urljoin(BASE_URL, endpoint)
        if params:
            url += '?' + urlencode(params)
        xbmc.log(f"Fetching URL: {url}", level=xbmc.LOGINFO)
        request = Request(url, headers={"User-Agent": "Kodi Addon", "Accept": "application/json"})
        response = urlopen(request, timeout=45)
        response_data = response.read()
        xbmc.log(f"Response Data: {response_data[:200]}...", level=xbmc.LOGINFO)
        return json.loads(response_data)
    except (URLError, socket.timeout) as e:
        xbmc.log(f"Error fetching data: {e}", level=xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Error', f'Error: {e}', xbmcgui.NOTIFICATION_ERROR)
        return None
    except Exception as e:
        xbmc.log(f"Unexpected error: {e}", level=xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Error', f'Unexpected error: {e}', xbmcgui.NOTIFICATION_ERROR)
        return None

def list_anime():
    xbmc.log("Starting list_anime()", level=xbmc.LOGINFO)
    xbmcplugin.setPluginCategory(handle=int(sys.argv[1]), category='Anime List')
    xbmcplugin.setContent(int(sys.argv[1]), 'videos')

    # Добавляем элемент поиска
    search_item = xbmcgui.ListItem(label='Поиск')
    search_url = build_url({'action': 'search'})
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=search_url, listitem=search_item, isFolder=True)

    anime_list = get_json_response("api/v1/anime/releases/latest")
    if anime_list:
        for anime in anime_list:
            if 'name' in anime and 'main' in anime['name']:
                title = anime['name']['main']
                genres = [genre['name'] for genre in anime.get('genres', [])]
                season = anime.get('season', {}).get('description', 'Unknown season')
                year = anime.get('year', 'Unknown year')
                anime_type = anime.get('type', {}).get('description', 'Unknown type')
                age_rating = anime.get('age_rating', {}).get('description', 'Unknown rating')
                poster_url = anime.get('poster', {}).get('optimized', {}).get('src', '')

                info = {
                    'title': title,
                    'genre': ', '.join(genres),
                    'season': season,
                    'year': year,
                    'type': anime_type,
                    'age_rating': age_rating,
                }

                list_item = xbmcgui.ListItem(label=title)
                list_item.setInfo('video', {
                    'title': title,
                    'genre': info['genre'],
                    'season': info['season'],
                    'year': info['year'],
                    'type': info['type'],
                    'age_rating': info['age_rating'],
                })
                if poster_url:
                    list_item.setArt({'poster': BASE_URL + poster_url})
                url = build_url({'action': 'details', 'anime_id': anime['id']})
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=list_item, isFolder=True)

    xbmc.log("Ending list_anime()", level=xbmc.LOGINFO)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def show_anime_details(anime_id):
    xbmc.log(f"Starting show_anime_details({anime_id})", level=xbmc.LOGINFO)
    anime = get_json_response(f"api/v1/anime/releases/{anime_id}")
    if anime:
        xbmcplugin.setPluginCategory(handle=int(sys.argv[1]), category='Anime Details')
        xbmcplugin.setContent(int(sys.argv[1]), 'videos')

        if 'name' in anime and 'main' in anime['name']:
            title = anime['name']['main']
            genres = [genre['name'] for genre in anime.get('genres', [])]
            season = anime.get('season', {}).get('description', 'Unknown season')
            year = anime.get('year', 'Unknown year')
            anime_type = anime.get('type', {}).get('description', 'Unknown type')
            age_rating = anime.get('age_rating', {}).get('description', 'Unknown rating')
            poster_url = anime.get('poster', {}).get('optimized', {}).get('src', '')

            info = {
                'title': title,
                'genre': ', '.join(genres),
                'season': season,
                'year': year,
                'type': anime_type,
                'age_rating': age_rating,
            }

            list_item = xbmcgui.ListItem(label=title)
            list_item.setInfo('video', {
                'title': title,
                'genre': info['genre'],
                'season': info['season'],
                'year': info['year'],
                'type': info['type'],
                'age_rating': info['age_rating'],
            })
            if poster_url:
                list_item.setArt({'poster': BASE_URL + poster_url})
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url='', listitem=list_item, isFolder=False)

            for episode in anime.get('episodes', []):
                episode_title = f"{episode['ordinal']} серия - {episode['name']}"
                episode_item = xbmcgui.ListItem(label=episode_title)
                episode_item.setInfo('video', {'title': episode_title})
                episode_item.setProperty('IsPlayable', 'false')
                url = build_url({'action': 'choose_quality', 'anime_id': anime_id, 'episode_ordinal': episode['ordinal']})
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=episode_item, isFolder=True)

            xbmcplugin.endOfDirectory(int(sys.argv[1]))
    xbmc.log(f"Ending show_anime_details({anime_id})", level=xbmc.LOGINFO)

def choose_quality(anime_id, episode_ordinal):
    xbmc.log(f"Starting choose_quality({anime_id}, {episode_ordinal})", level=xbmc.LOGINFO)
    anime = get_json_response(f"api/v1/anime/releases/{anime_id}")
    if anime:
        episodes = anime.get('episodes', [])
        for episode in episodes:
            if episode['ordinal'] == episode_ordinal:
                qualities = []
                if 'hls_480' in episode and episode['hls_480']:
                    qualities.append(('480p', episode['hls_480']))
                if 'hls_720' in episode and episode['hls_720']:
                    qualities.append(('720p', episode['hls_720']))
                if 'hls_1080' in episode and episode['hls_1080']:
                    qualities.append(('1080p', episode['hls_1080']))

                for quality, url in qualities:
                    quality_item = xbmcgui.ListItem(label=f"{episode['ordinal']} серия - {quality}")
                    quality_item.setInfo('video', {'title': quality})
                    quality_item.setProperty('IsPlayable', 'true')
                    play_url = build_url({'action': 'play', 'video_url': url})
                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=play_url, listitem=quality_item, isFolder=False)

        xbmcplugin.endOfDirectory(int(sys.argv[1]))
    xbmc.log(f"Ending choose_quality({anime_id}, {episode_ordinal})", level=xbmc.LOGINFO)

def play_anime(video_url):
    xbmc.log(f"Starting play_anime({video_url})", level=xbmc.LOGINFO)
    play_item = xbmcgui.ListItem(path=video_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=play_item)
    xbmc.log(f"Ending play_anime({video_url})", level=xbmc.LOGINFO)

def search_anime(query):
    xbmc.log(f"Starting search_anime({query})", level=xbmc.LOGINFO)
    xbmcplugin.setPluginCategory(handle=int(sys.argv[1]), category='Search Results')
    xbmcplugin.setContent(int(sys.argv[1]), 'videos')

    search_results = get_json_response("api/v1/app/search/releases", {'query': query})
    if search_results:
        for anime in search_results:
            if 'name' in anime and 'main' in anime['name']:
                title = anime['name']['main']
                genres = [genre['name'] for genre in anime.get('genres', [])]
                season = anime.get('season', {}).get('description', 'Unknown season')
                year = anime.get('year', 'Unknown year')
                anime_type = anime.get('type', {}).get('description', 'Unknown type')
                age_rating = anime.get('age_rating', {}).get('description', 'Unknown rating')
                poster_url = anime.get('poster', {}).get('optimized', {}).get('src', '')

                info = {
                    'title': title,
                    'genre': ', '.join(genres),
                    'season': season,
                    'year': year,
                    'type': anime_type,
                    'age_rating': age_rating,
                }

                list_item = xbmcgui.ListItem(label=title)
                list_item.setInfo('video', {
                    'title': title,
                    'genre': info['genre'],
                    'season': info['season'],
                    'year': info['year'],
                    'type': info['type'],
                    'age_rating': info['age_rating'],
                })
                if poster_url:
                    list_item.setArt({'poster': BASE_URL + poster_url})
                url = build_url({'action': 'details', 'anime_id': anime['id']})
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=list_item, isFolder=True)

    xbmc.log("Ending search_anime()", level=xbmc.LOGINFO)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def show_search_dialog():
    kb = xbmc.Keyboard('', 'Поиск аниме')
    kb.doModal()
    if kb.isConfirmed():
        query = kb.getText()
        if query:
            search_anime(query)

def router(paramstring):
    xbmc.log(f"Routing params: {paramstring}", level=xbmc.LOGINFO)
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'list':
            list_anime()
        elif params['action'] == 'details':
            show_anime_details(params['anime_id'])
        elif params['action'] == 'choose_quality':
            choose_quality(params['anime_id'], int(params['episode_ordinal']))
        elif params['action'] == 'play':
            play_anime(params['video_url'])
        elif params['action'] == 'search':
            show_search_dialog()
    else:
        list_anime()

if __name__ == '__main__':
    router(sys.argv[2][1:])
