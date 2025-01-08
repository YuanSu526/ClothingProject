import scrapy
from scrapy.selector import Selector
from scrapy_playwright.page import PageMethod
from urllib.parse import urlsplit, urlunsplit
import html

class cosSpider(scrapy.Spider):
    name = "cosSpider"

    custom_settings = {
        "DUPEFILTER_CLASS": "scrapy.dupefilters.BaseDupeFilter",
        "DEPTH_LIMIT": 0,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": False,
        },
        "PLAYWRIGHT_CONTEXT_ARGS": {
            "permissions": [],  # Disable location requests
            "geolocation": {"latitude": 0, "longitude": 0}
        },
        "CONCURRENT_REQUESTS": 5,
        "DOWNLOAD_TIMEOUT": 30,
        "FEED_OVERWRITE": True,
    }

    def start_requests(self):
        url = "https://www.cos.com/en/men/view-all.html"
        yield scrapy.Request(
            url,
            meta=dict(
                playwright=True,
                playwright_include_page=True,
                playwright_page_methods=[
                    PageMethod('wait_for_selector', 'div.ot-sdk-container'),
                    # Accept only required cookies
                    PageMethod("evaluate", """() => {
                        const closeButton = document.querySelector('button[id="onetrust-reject-all-handler"]');
                        if (closeButton) closeButton.click();
                    }"""),    
                    PageMethod('wait_for_selector', 'div.o-lightbox.is-newsletter-popup.is-open'),                
                    # Close newsletter pop-up
                    PageMethod("click", "button.a-button-nostyle.m-button-icon.a-icon-close"),
                    PageMethod('wait_for_timeout', 200),
                ],
            ),
            callback=self.parse_product_list,
        )


    async def parse_product_list(self, response):

        pagination_links = response.css('nav[role="navigation"] a::attr(href)').getall()

        self.logger.info(f"Extracted pagination links: {pagination_links}")

        




    


    async def errback(self, failure):

        page = failure.request.meta.get("playwright_page")  # Safely get the page

        if page:

            await page.close()  # Close the page if it exists

        else:

            self.logger.error("No Playwright page object found in the request meta.")