import scrapy
from scrapy.selector import Selector
from scrapy_playwright.page import PageMethod
from urllib.parse import urlsplit, urlunsplit
import urllib.parse
import html

class cosSpider(scrapy.Spider):
    name = "cosSpider"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.cos.com/",
    }

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
            headers=self.headers,
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

        page_numbers = [int(link.split('=')[-1]) for link in pagination_links if 'page=' in link]

        last_page_number = 1

        if page_numbers:

            last_page_number = max(page_numbers)

        self.logger.info(f"Processing {last_page_number} pages")

        for page_number in range(1, last_page_number + 1):

            pagination_url = f"https://www.cos.com/en/men/view-all.html?page={page_number}"

            yield scrapy.Request(
                url=pagination_url,
                headers=self.headers,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_page_methods=[
                        PageMethod('wait_for_selector', 'div.o-category-listing'),
                        PageMethod('wait_for_timeout', 200),
                    ],
                ),
                callback=self.parse_products,
            )



    # HELPER for constructing image URL
    def construct_image_url(self, img_element):
        # Extract `src` and `data-resolvechain` from the `img` element
        image_src = img_element.css('::attr(src)').get()

        if not image_src:
            return None  # Handle cases where no image src is found

        base_url = f"https:{image_src.split('?')[0]}" if image_src.startswith("//") else image_src.split('?')[0]

        resolve_chain = img_element.css('::attr(data-resolvechain)').get()

        if resolve_chain:
            # Extract the actual image source path from `data-resolvechain`
            source_image = resolve_chain.split("source[")[1].split("]")[0]
            encoded_source = urllib.parse.quote(source_image)

            # Construct query parameters for the final image URL
            params = [
                f"set=key[resolve.pixelRatio],value[4]",
                f"set=key[resolve.width],value[1200]",
                f"set=key[resolve.height],value[10000]",
                f"set=key[resolve.imageFit],value[containerwidth]",
                f"set=key[resolve.allowImageUpscaling],value[0]",
                f"set=key[resolve.format],value[jpg]",
                f"set=key[resolve.quality],value[100]",
                f"set=ImageVersion[1],origin[dam],source[{encoded_source}],type[DESCRIPTIVESTILLLIFE]"
            ]

            query_string = "&".join(params)
            full_image_url = f"{base_url}?{query_string}&call=url[file:/product/dynamic.chain]"

            return full_image_url
        else:
            return f"https:{image_src}" if image_src.startswith("//") else image_src



    async def parse_products(self, response):

        products = response.css('.o-category-listing .o-product')
                
        self.logger.info(f"Collected {len(products)} products from page: {response.url}")

        for product in products:

            product_name = product.css('h2.product-title::text').get()

            product_img_element = product.css('img.hover-image')

            product_image_src = self.construct_image_url(product_img_element)

            model_img_element = product.css('img.default-image')

            model_image_src = self.construct_image_url(model_img_element)

            product_color = product.css('span.colorName::text').get()

            product_link = product.css('div.description a.a-link.no-styling::attr(href)').get()

            if product_link:

                full_url = response.urljoin(product_link)

                yield scrapy.Request(
                    full_url,
                    headers=self.headers,
                    meta=dict(
                        playwright=True,
                        playwright_include_page=True,
                        playwright_page_methods=[
                            PageMethod("wait_for_selector", "div.description-wrapper"),
                        ],
                        product_name = product_name,
                        product_image_src = product_image_src,
                        model_image_src = model_image_src,
                        product_color=product_color
                    ),
                    callback=self.parse_product_detail,
                )

        page = response.meta.get("playwright_page")

        if page:

            await page.close()



    async def parse_product_detail(self, response):

        product_name = response.meta.get('product_name')

        product_image_src = response.meta.get('product_image_src')

        model_image_src = response.meta.get('model_image_src')

        product_color = response.meta.get('product_color')

        product_composition = ''

        product_composition_div = response.xpath('//div[contains(@class, "o-accordion")][.//h3[text()="DETAILS"]]')

        product_composition = product_composition_div.css('span.productCompositionSpan::text').get()

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