import os
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class ConfigDB(Enum):
    DB = os.getenv("DB")
    USERDB = os.getenv("USERDB")
    PASSWORDDB = os.getenv("PASSWORDDB")
    NAME_SERVICEDB = os.getenv("NAME_SERVICEDB")
    PORT = os.getenv("PORT")
    NAMEDB = os.getenv("NAMEDB")
    DATABASE_URL = f"{DB}://{USERDB}:{PASSWORDDB}@{NAME_SERVICEDB}:{PORT}/{NAMEDB}"


class RefineLevel(Enum):
    BASIC = 0
    INTERMEDIATE = 1
    ADVANCED = 2

class OutputMovieKeys(Enum):
    TITLE = 'title'
    ALT_TITLE = 'alternate_title'
    RATING = 'rating'
    DURATION = 'duration'
    MOVIE_URL = 'movie_url'
    MOVIE_ID = 'movie_id'
    DATE_PUBLISHED = 'date_published'
    ACTORS = 'actors'
    METASCORE = 'metascore'
    INFO_MOVIE = 'info_movie'

class MovieJsonKeys(Enum):
    NAME = 'name'
    ALT_NAME = 'alternateName'
    AGGREGATE_RATING = 'aggregateRating'
    RATING_VALUE = 'ratingValue'
    DURATION = 'duration'
    URL = 'url'
    DATE_PUBLISHED = 'datePublished'
    ACTOR = 'actor'

class ConfigImdb(Enum):
    PYTHON_BASE = Path(os.getenv("PYTHONPATH", Path(__file__).resolve().parent))
    DATA_PATH = PYTHON_BASE / "data"
    OUTPUT_DOCUMENT_NAME_PAGE = "movies_info.json"
    OUTPUT_DOCUMENT_NAME_REFINE = "movies_info_refine.csv"
    TOTAL_SCRAPY = 50  # cantidad de items scrapy

    BASE_URL = "https://www.imdb.com/"
    TOP_MOVIE_URL = "https://www.imdb.com/chart/top/"

    HEADERS = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "es-419,es;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    }

    COOKIES = {
        "session-id": "147-7675808-5557626",
        "session-id-time": "2082787201l",
        "ubid-main": "130-5751397-4856454",
        "ad-oo": "0",
        "aws-waf-token": "2547a2f3-2d2b-4403-adbd-81bca45fcb37:EQoAo85qnwYKAAAA:5EL5fJUrc1JQyW46mZTKc5/3YhRWNxftN5XnyqTdKiLEJawIyp/S530HygqGXO++fHiC4Y5FvTNOVvUF5IKCJRYWZBHlYlkZ0myDq051uXt3auDKsu52hrie5GqVcPgaOmqIYQ6FZ6xlGG7vZGmN1NtYyRL0ZQWGgoRl/k8IwdFzcUZ7vg6Yp3DnCtWGorM=",
        "international-seo": "es",
        "_cc_id": "87c5cf44f3c089e88b27c2d2d932891b",
        "panoramaId_expiry": "1753629450168",
        "panoramaId": "a514bfa3d1f1242a7e048d27f119a9fb927a7756d4e484cf3330ea8e799a71ea",
        "panoramaIdType": "panoDevice",
        "_au_1d": "AU1D-0100-001753543050-EMSQ81U3-AZSO",
        "_lr_geo_location_state": "TX",
        "_lr_geo_location": "US",
        "_ga_FVWZ0RM4DH": "GS2.1.s1753544099$o1$g0$t1753544099$j60$l0$h0",
        "_ga": "GA1.1.1712486414.1753544100",
        "session-token": "p3OFQkfyiY3mCn1UXEIu5y3gEnVD8eW9DNqIm0zb2cdEwcdXxT7DgyStLY00xw01AYm/kdAhYWjx8ndksT29rokj/HJJYCR4+bH/HknzsIhVxvfOtT+p91Yh7iCiDckk4Z9V/J+lARMYW1i5B9YeYdrhRRjjnd66lM0HV8xzXaFF4+pN9uWG3bRmjWUP8tNm+hNLF4w868dAVjjhyhv2WsrwXTs+W3NVNQoiloHY5Msl8ASBA+NwsRTZMi9cB+X2Ml+ZGZy4HNShqMK9VdnRc3coCpo1IkdMp9T57UXnYnZI5YinTz+u4FjdSdIIRhPGNaoUDQCOnaBieV1kHrKnPloUVZR+68PX",
        "ci": "eyJpc0dkcHIiOmZhbHNlfQ",
        "__gads": "ID=64807c8ef7f36654:T=1753543049:RT=1753544129:S=ALNI_MaHc3A_Gu5mIKO4xwvyK_WE05HeOQ",
        "__gpi": "UID=00001241b5b112d4:T=1753543049:RT=1753544129:S=ALNI_MYIpxnR6bq8k0L7zralDS3iNYLmOQ",
        "__eoi": "ID=6eb03655acb2b355:T=1753543049:RT=1753544129:S=AA-AfjbDGLGKNKdRipi2HSAFV9Gq",
        "__qca": "P1-6a7cff18-bb54-4816-af04-83802225fdea",
        "csm-hit": "tb:s-J9YKHN0FKFE4K5Y64ZS5|1753544152807&t:1753544153744&adb:adblk_no",
    }

    XPATH_JSON_INFO = "//script[@type='application/ld+json']//text()"


class ConfigRefine(Enum):
    DATA_TYPE = {
        "title": "string",
        "alternate_title": "string",
        "rating": "float32",
        "duration": "string",
        "movie_url": "string",
        "movie_id": "string",
        "metascore": "Int16",
        "actors": "object",
    }
    OUTPUT_COLUMNS = [
        "title",
        "date_published",
        "rating",
        "duration_minutes",
        "metascore",
        "actors",
        "movie_url",
    ]
