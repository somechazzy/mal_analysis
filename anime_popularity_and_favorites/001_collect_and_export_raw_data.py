import re
from time import sleep
import json
from bs4 import BeautifulSoup
from requests import request
from .misc import Status, AnimeType

BASE_URL = "https://myanimelist.net/topanime.php?type=bypopularity&limit="
MAX_LIMIT_OFFSET = 1400
OUTPUT_FILE_PATH = "output/anime_popularity_and_favorites_raw.json"


def get_anime_urls():
    print("Grabbing URLS...")
    limit_offset = 0
    urls = []
    while limit_offset <= MAX_LIMIT_OFFSET:
        sleep(3)
        print(f"\tOn offset {limit_offset}/{MAX_LIMIT_OFFSET}")
        url = BASE_URL + str(limit_offset)
        listing_page_response = request("GET", url)
        if listing_page_response.status_code != 200:
            print("Faced a non-200 response while grabbing URLs. Sleeping and retrying in 30 secs...")
            sleep(30)
            continue
        soup = BeautifulSoup(listing_page_response.text, features="lxml")
        anime_entries = soup.select(".fs14.fw-b")
        for anime_entry in anime_entries:
            anime_entry_str = str(anime_entry)
            anime_url = anime_entry_str[anime_entry_str.index("https"):
                                        anime_entry_str.index("\"", anime_entry_str.index("https"))]
            urls.append(anime_url)
        limit_offset += 50
    print("Grabbed URLS.\n-------------------------")
    return urls


def get_anime_stats_dict(urls):
    print("Grabbing info and creating dict...")
    anime_dict = {}
    for index, url in enumerate(urls, 1):
        title, members_dict, favorites, status, type_of_anime = get_anime_info(url)
        if members_dict.get("completed") == 0:
            fav_completed_percentage = 0
        else:
            fav_completed_percentage = round(favorites*100/members_dict.get("completed"), 4)
        anime = {
            "title": title,
            "members_dict": members_dict,
            "favorites": favorites,
            "fav_completed_%": fav_completed_percentage,
            "fav_total_%": round(favorites*100/members_dict.get("total"), 4),
            "popularity_rank": index,
            "url": url,
            "status": status,
            "type": type_of_anime
        }
        anime_id = url[url.index("anime/")+6:url.index("/", url.index("anime/")+6)]
        anime_dict[anime_id] = anime
        if index % 15 == 0:
            print(f"\tFinished {index} anime pages out of {len(urls)}")
        sleep(3)
    print("Grabbed info and created dict.\n-------------------------")
    return anime_dict


def get_anime_info(url):
    response = request("GET", url+"/stats")
    if response.status_code != 200:
        print("Faced a non-200 response while grabbing manga info. Sleeping and retrying in 30 secs...")
        sleep(30)
        response = request("GET", url)
    soup = BeautifulSoup(response.text, features="lxml")
    title_selection = soup.select(".h1_bold_none strong")
    try:
        title_select_0 = str(title_selection[0])
        if title_select_0.__contains__("title-english"):
            title_select_0 = title_select_0[:title_select_0.find("<span class=\"title-english\"")]
        title = re.sub("<[^>]*>", "", title_select_0).replace('&amp;', '&')
    except:
        print(f"Error getting title for {url}")
        title = ""

    members_info_selection = soup.select(".js-scrollfix-bottom-rel > .spaceit_pad")
    members_dict = get_members_dict_from_selection(members_info_selection)
    if -1 in members_dict.values():
        print(f"FAILED PARSING MEMBER NUMBERS FOR {url}. MEMBERS DICT={members_dict}")
    favorites_str, airing_str, type_str = get_favorites_and_airing_status_and_type_from_html(response.text)
    try:
        favorites = int(favorites_str)
    except:
        print(f"FAILED PARSING FAVORITES FOR {url}."
              f"FAVORITES_STR='{favorites_str}'.")
        favorites = 0
    if airing_str.lower().__contains__("finished"):
        status = Status.FINISHED
    elif airing_str.lower().__contains__("currently"):
        status = Status.AIRING
    else:
        status = Status.YET_TO_AIR

    if type_str.lower().__contains__("tv"):
        type_of_anime = AnimeType.SERIES
    elif type_str.lower().__contains__("movie"):
        type_of_anime = AnimeType.MOVIE
    else:
        type_of_anime = AnimeType.ELSE

    return title, members_dict, favorites, status, type_of_anime


def get_favorites_and_airing_status_and_type_from_html(text):
    starting_index = text.find("<h2>Information</h2>")

    external_header_exists = text.__contains__("External Links")
    if external_header_exists:
        ending_index = text.find("External Links", starting_index)
    else:
        ending_index = text.find("<br />", text.find("<h2>Statistics</h2>"))
    info_text = text[starting_index:ending_index]

    divs = []
    while True:
        starting_index = info_text.find("<div")
        ending_index = info_text.find("</div>") + 6
        div = info_text[starting_index:ending_index]
        divs.append(div)
        info_text = info_text[ending_index:]
        if not info_text.__contains__("<div>"):
            break
    divs.append("?")

    def find_attribute_index(divs_, attribute):
        for i in range(0, len(divs_)):
            if divs_[i].__contains__(attribute):
                return i
        return -1

    favorites_str_selection = re.sub("<[^>]*>", "", divs[find_attribute_index(divs, "Favorites")])
    favorites_str = re.sub("[^0-9]", "", favorites_str_selection).strip()  # type

    airing_str = re.sub("<[^>]*>", "", divs[find_attribute_index(divs, "Status")])
    type_str = re.sub("<[^>]*>", "", divs[find_attribute_index(divs, "Type")])

    return favorites_str, airing_str, type_str


def get_members_dict_from_selection(members_info_selection):
    watching = -1
    completed = -1
    on_hold = -1
    dropped = -1
    ptw = -1
    total = -1

    def get_numeric_value(html_snippet):
        value_with_label = re.sub("<[^>]*>", "", str(html_snippet))
        value_str = re.sub("[^0-9]", "", str(value_with_label))
        try:
            value = int(value_str)
        except:
            value = -1
        return value

    for selection in members_info_selection:
        if str(selection).__contains__("Watching"):
            watching = get_numeric_value(str(selection))
        if str(selection).__contains__("Completed"):
            completed = get_numeric_value(str(selection))
        if str(selection).__contains__("On-Hold"):
            on_hold = get_numeric_value(str(selection))
        if str(selection).__contains__("Dropped"):
            dropped = get_numeric_value(str(selection))
        if str(selection).__contains__("Plan to Watch"):
            ptw = get_numeric_value(str(selection))
        if str(selection).__contains__("Total"):
            total = get_numeric_value(str(selection))
    members_dict = {
        "watching": watching,
        "completed": completed,
        "on_hold": on_hold,
        "dropped": dropped,
        "ptw": ptw,
        "total": total,
    }
    return members_dict


anime_urls = get_anime_urls()
final_dict = get_anime_stats_dict(anime_urls)

'''
example final dict:

{
    "11757": {
        "title": "Sword Art Online",
        "members_dict": {
            "watching": 50000,
            "completed": 500000,
            "on_hold": 15000,
            "dropped": 2000,
            "ptw": 33000,
            "total": 600000,
        },
        "favorites": 5000,
        "fav_completed_%": 1.0000,
        "fav_total_%": 0.8333,
        "popularity_rank": 150,
        "url": "https://myanimelist.net/anime/11757/Sword_Art_Online",
        "status": "finished",
        "type": "series"
    }
}
'''

print("Printing to file...")
with open(OUTPUT_FILE_PATH, 'w') as file:
    file.write(json.dumps(final_dict))
