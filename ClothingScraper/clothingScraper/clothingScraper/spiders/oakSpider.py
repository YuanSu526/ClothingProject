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
                    PageMethod('wait_for_selector', 'div.site-container'),
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

        #Scroll To The Bottom To View All The Items
        page = response.meta['playwright_page']

        current_page_num = 1  #First 2 pages are already loaded

        max_pages = 5  #Stop after reaching page 15 or no new products are loaded
        
        for _ in range(current_page_num, max_pages + 1):

            await page.evaluate('window.scrollBy(0,document.body.scrollHeight)')

            more_product_button = await page.query_selector("button:has-text('View More Products')")

            if more_product_button:

                # Check if the button is disabled
                is_disabled = await more_product_button.get_attribute("disabled")
                if is_disabled is None:  # If disabled attribute does not exist, the button is enabled
                    print("Button is enabled. Clicking it...")
                    await more_product_button.click()
                else:
                    print("Button is disabled. Breaking out of loop.")
                    break
            else:
                print("Button not found. Breaking out of loop.")
                break


        # Smooth scroll from bottom to top
        await page.evaluate('''
            // Smoothly scroll back up
            (function(targetPosition, duration) {
                const startPosition = window.scrollY;  // Current position at the bottom
                const distance = targetPosition - startPosition;  // Distance to scroll (from bottom to top)
                let startTime = null;

                function animationStep(currentTime) {
                    if (!startTime) startTime = currentTime;  // Set the start time
                    const elapsedTime = currentTime - startTime;
                    const ease = Math.min(elapsedTime / duration, 1);  // Ensure easing value stays within 0 and 1
                    const newScrollY = startPosition + (distance * ease);  // Calculate the new scroll position
                    window.scrollTo(0, newScrollY);  // Scroll to the new position

                    if (elapsedTime < duration) {
                        requestAnimationFrame(animationStep);  // Continue scrolling
                    } else {
                        window.scrollTo(0, targetPosition);  // Ensure exact target position (at the top)
                    }
                }

                requestAnimationFrame(animationStep);
            })(0, 10000);  // Scroll back up to the top over 10 seconds
        ''')
        
        await page.wait_for_timeout(3000)  # Wait for the smooth scroll to complete

        #Renew The Product List After Scrolling

        content = await page.content()
        
        response = scrapy.http.HtmlResponse(url=page.url, body=content, encoding='utf-8')

        products = response.css('div.collection__grid div.collection__grid-item')

        for product in products:

            product_link = product.css('a.collection-item__image-link::attr(href)').get()

            print(product_link)
