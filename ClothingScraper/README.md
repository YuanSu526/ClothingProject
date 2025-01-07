# Clothing Data Scraper

This scraper is written in **Python 3.13.1** and is designed to collect clothing data such as name, color, composition, images, and model images from various clothing websites.

## Setup Instructions

To replicate the scraper, follow these steps:

1. **Clone the Repository**  
   Ensure you have the repository downloaded locally.

2. **Navigate to the Scraper Folder**  
   Move into the `ClothingScraper` directory (where this README.md is located at):

3. **Create a Virtual Environment**
   Create and activate a virtual environment to isolate dependencies:
   ```
    python3 -m venv venv
    source venv/bin/activate  #For Linux/macOS
    venv\Scripts\activate     #For Windows
   ```

4. **Install Required Libraries**
    Use the `requirements.txt` file to install all necessary dependencies:
    ```
    pip install -r requirements.txt
    ```

5. **Navigate to the clothingScraper subfolder**  
   Move into the `clothingScraper` directory (where `spiders` folder is located at):
    ```
    cd clothingScraper
    ```

6. **Run the Scraper**
    Each scraper in the spiders folder is named as `brandNameSpider.py`, execute the scraper script to begin collecting data:
    ```
    scrapy crawl brandNameSpider -o output.json
    ```
    Note that calling multiple scraper and outputing to the same `output.json` file may overwrite existing clothing data.
    If scrapy is not callable, download the corresponding library:
    ```
    pip install scrapy
    ```
