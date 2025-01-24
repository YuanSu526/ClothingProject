import scrapy
from scrapy.selector import Selector
from scrapy_playwright.page import PageMethod
from urllib.parse import urlsplit, urlunsplit, urlparse
import html


class uniqloSpider(scrapy.Spider):

    name = "uniqloSpider"

    custom_settings = {
        "DUPEFILTER_CLASS": "scrapy.dupefilters.BaseDupeFilter",  # Disable duplicate filtering
        "DEPTH_LIMIT": 0,  # Unlimited crawling depth
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": False,
        },
        "CONCURRENT_REQUESTS": 2,
        "DOWNLOAD_TIMEOUT": 60,  # Increase download timeout
        "COOKIES_ENABLED": True,  # Preserve cookies across requests
        "FEED_OVERWRITE": True,
    }


    def start_requests(self):

        url = "https://www.uniqlo.com/ca/en/men"

        yield scrapy.Request(

            url,

            meta=dict(
                playwright=True,
                playwright_include_page=True,
                playwright_page_methods=[
                    PageMethod('wait_for_timeout', 5000),
                ]
            ),

            callback=self.parse_category_list,
        )


    #Helper
    async def remove_query_from_url(self, url):

        if url:

            split_url = urlsplit(url)

            cleaned_url = urlunsplit((split_url.scheme, split_url.netloc, split_url.path, '', '')) 

            return cleaned_url
        
        return url


    async def parse_category_list(self, response):

        # Extract Product Links From The Product List Page ================================================================================

        #Scroll To The Bottom To View All The Items
        page = response.meta['playwright_page']

        content = await page.content()
        
        response = scrapy.http.HtmlResponse(url=page.url, body=content, encoding='utf-8')

        categories = response.css('div.class-list__wrapper div.class-list__category-list-wrapper > div div.category-list')

        category_links = []

        for category in categories:

            links = category.css('a::attr(href)')

            if '/men/' not in links[0].get():
                
                continue

            min_l = len(links[0].get())

            index = 0

            for i in range(0,len(links)):

                if len(links[i].get()) < min_l:

                    min_l = len(links[i].get())

                    index = i

            category_links.append(links[index].get())

        # category_link = category_links[1]

        for category_link in category_links:

            full_url = response.urljoin(category_link)

            yield scrapy.Request(
                full_url,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_page_methods=[
                        PageMethod("wait_for_load_state", "networkidle"),
                    ],
                ),
                callback=self.parse_product_list,
            )

        if page:

            await page.close()


    async def parse_product_list(self, response):

        page = response.meta['playwright_page']

        while True:
            try:
                if await page.is_visible("a > div.fr-load-more"):
                    await page.click("a > div.fr-load-more")
                    await page.wait_for_timeout(1000)
                else:
                    break
            except Exception as e:
                break

        content = await page.content()
        
        response = scrapy.http.HtmlResponse(url=page.url, body=content, encoding='utf-8')

        products = response.css('div.fr-contents-card article')

        # product = products[1]

        for product in products:

            product_link = product.css('a::attr(href)').get()
            
            if product_link:

                full_url = response.urljoin(product_link)

                yield scrapy.Request(
                    full_url,
                    meta=dict(
                        playwright=True,
                        playwright_include_page=True,
                        playwright_page_methods=[
                            PageMethod("goto", full_url, wait_until="domcontentloaded"),
                            PageMethod("wait_for_selector", "dd.fr-definition-list-description"),
                        ],
                    ),
                    callback=self.parse_product_detail,
                )

        if page:

            await page.close()

    async def parse_product_detail(self, response):

        product_name = response.css('h1.fr-head span.title::text').get()

        product_composition = response.css('dd.fr-definition-list-description::text').get()

        #Getting product image src aka
        #First image with 'WesternCommon' in the keyword
        image_srcs = response.css('div.media-gallery--ec-renewal img::attr(src)').getall()

        western_common_images = [src for src in image_srcs if 'WesternCommon' in src]

        product_image_src = western_common_images[0] if western_common_images else "No WesternCommon image found"

        product_image_src = await self.remove_query_from_url(product_image_src)

        print(product_image_src)

        chip_colors = response.css('div[data-test="product-picker"] div.fr-chip-wrapper-er span.fr-implicit::text').getall()

        #Iterating through all color buttons
        page = response.meta['playwright_page']

        await page.wait_for_selector('div[data-test="product-picker"]')

        chips = await page.query_selector_all('div[data-test="product-picker"] label.fr-chip-label.color')

        for i in range(0, len(chips)):

            chip = chips[i]

            await chip.click()

            await page.wait_for_timeout(500)

            model_image_src = await page.evaluate("""
                () => {
                    const firstImg = document.querySelector('div.media-gallery--ec-renewal--grid img');
                    return firstImg ? firstImg.src : '';
                }
            """)

            model_image_src = await self.remove_query_from_url(model_image_src)

            product_color = chip_colors[i] if i < len(chip_colors) else ''

            print(product_color)

            print(f"Model image src: {model_image_src}")

            yield {
                'name': product_name,
                'image': product_image_src,
                'model': model_image_src,
                'color': product_color,
                'color_variations': [],
                'composition': product_composition,
            }

        page = response.meta.get("playwright_page")

        if page:

            await page.close()