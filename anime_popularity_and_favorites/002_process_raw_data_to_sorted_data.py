import json

from anime_popularity_and_favorites.misc import Status, AnimeType

INPUT_FILE_PATH = "output/anime_popularity_and_favorites_raw.json"
OUTPUT_FILE_PATH_SORTED_BY_TOTAL = "output/anime_popularity_and_favorites_sorted_total.json"
OUTPUT_FILE_PATH_SORTED_BY_COMPLETED = "output/anime_popularity_and_favorites_sorted_completed.json"
OUTPUT_FILE_PATH_SORTED_BY_COMPLETED_PLUS_WATCHING = \
    "output/anime_popularity_and_favorites_sorted_completed_plus_watching.json"
OUTPUT_FILE_PATH_SORTED_BY_COMPLETED_PLUS_WATCHING_WITH_MOVIES= \
    "output/anime_popularity_and_favorites_sorted_completed_plus_watching_with_movies.json"

def get_json_text():
    with open(INPUT_FILE_PATH, 'r') as file_in:
        text = file_in.read()
    return text


class AnimeEntry:
    def __init__(self, anime_id, anime_title, url, members_total, members_completed, members_completed_plus_watching,
                 favorites, fav_to_total, fav_to_completed, status, type_of_anime, popularity_rank):
        self.anime_id = anime_id
        self.anime_title = anime_title
        self.url = url
        self.members_total = members_total
        self.members_completed = members_completed
        self.members_completed_plus_watching = members_completed_plus_watching
        self.favorites = favorites
        self.fav_to_total = fav_to_total
        self.fav_to_completed = fav_to_completed
        self.fav_to_completed_plus_watching = round(favorites*100/members_completed_plus_watching, 4)
        self.status = status
        self.type_of_anime = type_of_anime
        self.popularity_rank = popularity_rank

    def __str__(self):
        return f"{self.anime_title} ({self.anime_id}): {self.members_total} members in total, {self.members_total} " \
               f"completed. {self.favorites} favorites. {self.fav_to_total}% favorites/total percentage. " \
               f"{self.fav_to_completed}% favorites/completed percentage. Airing? {self.status}."


def populate_anime_array_from_dict(_anime_dict: dict):
    anime_array = []
    for _anime_id, anime_details in _anime_dict.items():
        anime_entry = AnimeEntry(int(_anime_id), anime_details.get("title", "No Title"), anime_details.get("url"),
                                 anime_details.get("members_dict").get("total"),
                                 anime_details.get("members_dict").get("completed"),
                                 anime_details.get("members_dict").get("completed") +
                                 anime_details.get("members_dict").get("watching"),
                                 anime_details.get("favorites"),
                                 anime_details.get("fav_total_%"), anime_details.get("fav_completed_%"),
                                 anime_details.get("status"), anime_details.get("type"),
                                 anime_details.get("popularity_rank"))
        anime_array.append(anime_entry)
    return anime_array


# def get_sorted_by_completed_anime_dict(_anime_entry_array: []):
#     anime_entry_array_sorted = sorted(_anime_entry_array, key=lambda x: x.fav_to_completed, reverse=True)
#     sorted_dict = {}
#     index = 0
#     for entry in anime_entry_array_sorted:
#         if entry.status in [Status.YET_TO_AIR, Status.AIRING]:
#             continue
#         sorted_dict[index + 1] = entry.__dict__
#         index += 1
#     return sorted_dict


def get_sorted_by_total_anime_dict(_anime_entry_array: []):
    anime_entry_array_sorted = sorted(_anime_entry_array, key=lambda x: x.fav_to_total, reverse=True)
    sorted_dict = {}
    for index, entry in enumerate(anime_entry_array_sorted):
        sorted_dict[index + 1] = entry.__dict__
    return sorted_dict


def get_sorted_by_completed_plus_watching_anime_dict(_anime_entry_array: [], with_movies=False):
    anime_entry_array_sorted = sorted(_anime_entry_array, key=lambda x: x.fav_to_completed_plus_watching, reverse=True)
    sorted_dict = {}
    index = 0
    for entry in anime_entry_array_sorted:
        if entry.status == Status.YET_TO_AIR or (entry.type_of_anime == AnimeType.MOVIE and not with_movies):
            continue
        sorted_dict[index + 1] = entry.__dict__
        index += 1
    return sorted_dict


json_text = get_json_text()
anime_dict = json.loads(json_text)
anime_entry_array = populate_anime_array_from_dict(anime_dict)
# sorted_completed_anime_dict = get_sorted_by_completed_anime_dict(anime_entry_array)
sorted_total_anime_dict = get_sorted_by_total_anime_dict(anime_entry_array)
sorted_completed_plus_watching_anime_dict = get_sorted_by_completed_plus_watching_anime_dict(anime_entry_array)
sorted_completed_plus_watching_with_movies_anime_dict =\
    get_sorted_by_completed_plus_watching_anime_dict(anime_entry_array, with_movies=True)

# with open(OUTPUT_FILE_PATH_SORTED_BY_COMPLETED, 'w') as file_out:
#     file_out.write(json.dumps(sorted_completed_anime_dict))

with open(OUTPUT_FILE_PATH_SORTED_BY_TOTAL, 'w') as file_out:
    file_out.write(json.dumps(sorted_total_anime_dict))

with open(OUTPUT_FILE_PATH_SORTED_BY_COMPLETED_PLUS_WATCHING, 'w') as file_out:
    file_out.write(json.dumps(sorted_completed_plus_watching_anime_dict))

with open(OUTPUT_FILE_PATH_SORTED_BY_COMPLETED_PLUS_WATCHING_WITH_MOVIES, 'w') as file_out:
    file_out.write(json.dumps(sorted_completed_plus_watching_with_movies_anime_dict))
