import scrapy
from scrapy.selector import Selector
from scrapy_playwright.page import PageMethod
from urllib.parse import urlsplit, urlunsplit
import html


class zaraSpider(scrapy.Spider):

    name = "zaraSpider"

    custom_settings = {
        "DUPEFILTER_CLASS": "scrapy.dupefilters.BaseDupeFilter",  # Disable duplicate filtering
        "DEPTH_LIMIT": 0,  # Unlimited crawling depth
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": False,
        },
        "CONCURRENT_REQUESTS": 5,
        "DOWNLOAD_TIMEOUT": 30,
        # "COOKIES_ENABLED": True,  # Preserve cookies across requests
        # "RETRY_TIMES": 5,  # Number of retries before giving up
        "FEED_OVERWRITE": True,
    }



    def start_requests(self):

        url = "https://www.zara.com/ca/en/man-all-products-l7465.html"

        yield scrapy.Request(

            url,

            meta=dict(
                playwright=True,
                playwright_include_page=True,
                playwright_page_methods=[
                    PageMethod('wait_for_selector', 'div.product-groups')
                ]
            ),

            callback=self.parse_product_list,
        )



    async def parse_product_list(self, response):

        #Extract Product Links From The Product List Page ================================================================================

        #Scroll To The Bottom To View All The Items
        page = response.meta['playwright_page']

        current_page_num = 2  #First 2 pages are already loaded

        max_pages = 9  #Stop after reaching page 15 or no new products are loaded

        for _ in range(current_page_num, max_pages + 1):

            await page.evaluate('window.scrollBy(0,document.body.scrollHeight)')

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

        products = response.css('ul.product-grid__product-list > li')

        print(f"Loading {len(products)} products")

        #Extract Product Links And Open Product Tabs

        for product in products:

            # Extract the actual image URL and pass it to product detail layer
            product_image_src = product.css('img.media-image__image::attr(src)').get()

            product_image_alt = product.css('img.media-image__image::attr(alt)').get()

            product_color = "unknown"

            if product_image_alt is not None:

                product_color = product_image_alt.split('-')[-1].strip()

            product_link = product.css('a.product-link::attr(href)').get()

            if product_link:

                full_url = response.urljoin(product_link)

                yield scrapy.Request(
                    full_url,
                    meta=dict(
                        playwright=True,
                        playwright_include_page=True,
                        playwright_page_methods=[
                            PageMethod("wait_for_load_state", "networkidle"),
                            PageMethod("wait_for_selector", "div.product-detail-extra-detail", timeout=5000),
                        ],
                        product_image_src=product_image_src,
                        product_color=product_color
                    ),
                    callback=self.parse_product_detail,
                    errback=self.errback
                )



    async def parse_product_detail(self, response):

        # Product Name Extraction ====================================================================================================

        product_name = response.css('h1.product-detail-info__header-name::text').get()

        # Product Color Extraction ====================================================================================================

        product_color_text = response.meta.get('product_color')

        #Get the color variations

        product_color_variations = []

        product_color_list = response.css('ul.product-detail-color-selector__colors > li')

        for color in product_color_list:

            #Getting the rgb value of each color variation

            div_style = color.css('div.product-detail-color-selector__color-area::attr(style)').get()

            if div_style:

                rgb_value = div_style.split('background-color:')[1].strip(' rgb();')

                product_color_variations.append(rgb_value)

        #Composition Extraction ==================================================================================================== 

        section = response.css('div.product-detail-extra-detail').get()

        if not section:

            self.logger.warning("Composition section not found!")

            composition_text = "Composition not found"

        else:

            selector = Selector(text=section)

            composition_text = selector.xpath('//span[normalize-space(text())="COMPOSITION"]/ancestor::div[1]/parent::*/div//span//text()').getall()

            composition_text = " ".join(composition_text).strip().replace("COMPOSITION", "").strip()

        # Product and Model Image Extraction ====================================================================================================

        #Helper
        def remove_query_from_url(url):

            if url:

                split_url = urlsplit(url)

                cleaned_url = urlunsplit((split_url.scheme, split_url.netloc, split_url.path, '', '')) 

                return cleaned_url
            
            return url

        #Locate the correct color button

        page = response.meta.get("playwright_page")

        target_color_button = None

        product_color_list = await page.query_selector_all('ul.product-detail-color-selector__colors > li')

        for color in product_color_list:

            current_color = await color.query_selector('span.screen-reader-text')

            current_color_text = await current_color.inner_text() if current_color else "no_color"

            if current_color_text.strip().lower() == product_color_text.strip().lower():

                target_color_button = await color.query_selector('button.product-detail-color-selector__color-button')

        if target_color_button:

            await target_color_button.click()

            await page.wait_for_load_state('networkidle')

        product_image_src = response.meta.get('product_image_src')

        model_image_src = ''

        image_set = response.css('picture.media-image source::attr(srcset)').get()

        if image_set:

            model_image_src = image_set.split(',')[0].split()[0]

        product_image_src = remove_query_from_url(product_image_src)

        model_image_src =  remove_query_from_url(model_image_src)

        yield {
            'name': product_name,
            'image': product_image_src,
            'model': model_image_src,
            'color': product_color_text,
            'color_variations': product_color_variations,
            'composition': composition_text,
        }

        if page:

            await page.close()



    async def errback(self, failure):

        page = failure.request.meta.get("playwright_page")  # Safely get the page

        if page:

            await page.close()  # Close the page if it exists

        else:

            self.logger.error("No Playwright page object found in the request meta.")