import scrapy
from scrapy.selector import Selector
from scrapy_playwright.page import PageMethod
from urllib.parse import urlsplit, urlunsplit, urlparse
import html


class oakSpider(scrapy.Spider):

    name = "oakSpider"

    custom_settings = {
        "DUPEFILTER_CLASS": "scrapy.dupefilters.BaseDupeFilter",  # Disable duplicate filtering
        "DEPTH_LIMIT": 0,  # Unlimited crawling depth
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": False,
        },
        "CONCURRENT_REQUESTS": 5,
        "DOWNLOAD_TIMEOUT": 30,
        "COOKIES_ENABLED": True,  # Preserve cookies across requests
        # "RETRY_TIMES": 5,  # Number of retries before giving up
        "FEED_OVERWRITE": True,
    }


    def start_requests(self):

        url = "https://oakandfort.ca/collections/all-mens"

        yield scrapy.Request(

            url,

            meta=dict(
                playwright=True,
                playwright_include_page=True,
                playwright_page_methods=[
                    # PageMethod('wait_for_selector', 'div.css-flq1iw', timeout = 5000),
                    # PageMethod("click", "button[id='closeIconContainer']"),
                    # PageMethod('wait_for_timeout', 500),
                    PageMethod('wait_for_selector', 'div.cookieconsent-wrapper'),
                    PageMethod("click", "button[aria-label='Accept']"),
                    PageMethod('wait_for_selector', 'div.shopify-section'),
                ]
            ),

            callback=self.parse_product_list,
        )


    #Helper
    async def remove_query_from_url(self, url):

        if url:

            split_url = urlsplit(url)

            cleaned_url = urlunsplit((split_url.scheme, split_url.netloc, split_url.path, '', '')) 

            return cleaned_url
        
        return url


    async def parse_product_list(self, response):

        # Extract Product Links From The Product List Page ================================================================================

        # Scroll To The Bottom To View All The Items
        page = response.meta['playwright_page']

        print("Success")