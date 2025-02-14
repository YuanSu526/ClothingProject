# Clothing Matching System

## Full Title
Recommend full-body outfits based on user preferences, weather, and occasion.

## Target Audience
Our app is designed for people who are into fashion but have not developed a structured clothing taste. Users can upload all of their clothes as pictures, and the system can recommend a few clothing combinations based on occasion and local weather. The app can also be linked to different clothing websites to recommend a shopping list if a user wishes to build new wardrobes.

## Main Problem
When people just get interested in fashion, they often do not know where to begin. It takes a lot of time and money for trial and error until they develop their unique taste in clothes. Most clothing websites’ recommendation systems only display clothes in a similar style; however, they usually do not provide inspiration for the whole outfit. With a clothing matching system, not only can fashion beginners develop a mature taste more easily, but clothing brands can also have a higher chance of selling their clothes in full sets.

## Main Actors
- **Fashionista**
- **Retailer**
- **Admins**

## Three Main Use Cases

### Case One: Inquire Outfit Suggestions Based on Users' Occasion
- **Description:**  
  Users clarify their preferences by clicking on buttons, dragging scales, and inputting numbers or texts. Then, they click on the “Generate Preference” button. A new page containing lists of outfit ideas will be displayed.

### Case Two: Browse Clothes Provided by Online Stores
- **Description:**  
  Users select a few pieces of clothing they wish to build their wardrobe around and click on the “Look for Matching Pieces from Stores” button. A new page containing lists of clothing pieces from different stores will be displayed.

### Case Three: Upload Outfits
- **Description:**  
  Users click on the clothing uploading section and get prompted to upload several images of clothes. For each clothing item, users may add additional information such as material, formal/casual style, and preference for wearing it more or less often. Once the “Confirm Uploading” button is clicked, the images, along with additional info, will be stored in the user’s online closet, which they can browse or edit.

---

# Project Planning

## Goals
1. **Scrape clothing data**: Collect relevant clothing details, including:
   - Name, Color, Composition, Image, and Model image

2. **Develop ML Algorithms**:  
   Implement different machine learning algorithms for various use cases, such as:
   - Outfit recommendation based on weather and occasion
   - Wardrobe expansion recommendations

3. **Develop System Components**:  
   - **Database**: Store user-uploaded clothes and scraped clothing data.
   - **Backend (BE)**: Host trained machine learning algorithm, store clothing data samples, and support FE-BE communication
   - **Frontend (FE)**: Create interface for uploading clothes, browsing recommendations, and viewing outfit suggestions.

## Current Stage

1. **Scraping Clothing Data (Done)**:  
   - **Completed**: Scraped data from: ZARA, COS, Massimo Dutti, and UNIQLO
   - **Overall**: 3.6k rows of data are collected, each with 5 columns (2 image, 2 word vecs, 1 categorial) a piece of sample data is placed in `<project_root>/ClothingData`, when one gets the crawler outputs they are recommended to place data in the same folder as well

2. **Cleaning Clothing Data and Adding Labels**:
   - **Completed**: Cleaned data using scripts
   - **TODO**: ML models to extract texture and precise color, determine occasion
   - **In Progress**: ML model to extract clothing outline
---

**To replicate this project, please first head to the ClothingScraper folder and follow the instruction over there.**