import scrapy


class ImdbMoviesItem(scrapy.Item):
    info_movie = scrapy.Field()
