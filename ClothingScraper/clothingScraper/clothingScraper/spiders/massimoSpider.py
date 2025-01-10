import scrapy
from scrapy.selector import Selector
from scrapy_playwright.page import PageMethod
from urllib.parse import urlsplit, urlunsplit, urlparse
import html


class massimoSpider(scrapy.Spider):

    name = "massimoSpider"

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

        url = "https://www.massimodutti.com/ca/s/m-view-all-n4451"

        yield scrapy.Request(

            url,

            meta=dict(
                playwright=True,
                playwright_include_page=True,
                playwright_page_methods=[
                    PageMethod('wait_for_selector', 'div.ot-sdk-container'),
                    # Accept only required cookies
                    PageMethod("evaluate", """() => {
                        const settingsButton = document.querySelector('button[id="onetrust-pc-btn-handler"]');
                        if (settingsButton) settingsButton.click();
                    }"""),    
                    PageMethod('wait_for_timeout', 500),
                    PageMethod('wait_for_selector', 'button.save-preference-btn-handler'),
                    PageMethod("click", 'button.save-preference-btn-handler'),
                    PageMethod('wait_for_selector', 'ul.grid-product-list'),
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

        for _ in range(0,2):

            await page.evaluate('window.scrollBy(0,document.body.scrollHeight)')

            await page.wait_for_timeout(1000)

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
                })(0, 30000);  // Scroll back up to the top over 10 seconds
            ''')

            await page.wait_for_timeout(30000)  # Wait for the smooth scroll to complete

        content = await page.content()
        
        response = scrapy.http.HtmlResponse(url=page.url, body=content, encoding='utf-8')

        products = response.css('ul.grid-product-list > li')

        print(f"Loading {len(products)} products")

        # product = products[0]

        for product in products:

            product_link = response.urljoin(product.css('a::attr(href)').get())
            
            product_color = product.css('button.product-color-tile::attr(title)').get()

            model_image_src = await self.remove_query_from_url(product.css('img::attr(src)').get())

            playwright_page_methods = [
                # Wait until the accordion loads
                PageMethod("wait_for_selector", "ul.accordion"),
                PageMethod("wait_for_selector", "div[id='product-color-selector']"),
            ]

            # Add the click step only if product_color is not None
            if product_color:
                playwright_page_methods.append(PageMethod("click", f"button[title='{product_color}']"))
                playwright_page_methods.append(PageMethod('wait_for_timeout', 3000))

            playwright_page_methods.extend([
                PageMethod("wait_for_selector", "div.cc-imagen-collection"),
                # Scroll within the image container
                PageMethod(
                    "evaluate",
                    """() => {
                        const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
                        const scrollContainer = async () => {
                            const imageContainer = document.querySelector('div.cc-imagen-collection');
                            if (imageContainer) {
                                for (let i = 0; i < 15; i++) {  // Scroll 15 times
                                    imageContainer.scrollBy(0, 500);
                                    await sleep(500);  // Wait 500ms between each scroll
                                }
                            }
                        };
                        scrollContainer();
                    }"""
                ),
                PageMethod('wait_for_timeout', 8000),
                # Click the FABRIC AND CARE section
                PageMethod("click", 'div.text-l span:has-text("FABRIC AND CARE")'),
                # Optionally wait for expanded content to load
                PageMethod('wait_for_timeout', 500),
            ])

            yield scrapy.Request(
                product_link,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_page_methods=playwright_page_methods,
                    model_image_src=model_image_src,
                    product_color=product_color
                ),
                callback=self.parse_product_detail,
            )



    async def parse_product_detail(self, response):

        product_name = response.css('h1.product-name::text').get()

        product_image_src = None

        model_image_src = None

        product_color = ''

        product_color_variations = []

        product_composition = ''

        # Product Color Extraction ====================================================================================================

        product_color_section = response.css("div[id='product-color-selector']")

        product_color = product_color_section.css('span::text').get()
        
        # Product Composition Extraction ====================================================================================================

        product_composition = response.css('div.sidebar-body div div.mb-12 *::text').getall()

        # Product and Model Image Extraction ====================================================================================================

        product_images = response.css('div.media-image.anim.cc-imagen-media img::attr(src)').getall()

        product_image_src = next((img for img in product_images if urlparse(img).path.endswith("o1.jpg")), None)

        if not product_image_src and len(product_images) >= 4:

            product_image_src = product_images[-4]

        product_image_src = await self.remove_query_from_url(product_image_src)

        model_image_src = product_images[0] if product_images else response.meta.get('model_image_src')

        model_image_src = await self.remove_query_from_url(model_image_src)

        yield {
            'name': product_name,
            'image': product_image_src,
            'model': model_image_src,
            'color': product_color,
            'color_variations': product_color_variations,
            'composition': product_composition,
        }

        page = response.meta.get("playwright_page")

        if page:

            await page.close()


