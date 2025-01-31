# Data Cleaning Scripts

This folder contains three main scripts:
- _clothingTypeExtraction
- _removingExcess
- _uploadImagesToGCP

These scripts are all written in javascript and executable in **node v18.17.1**.  
They aim to find out all the clothing types from the scraped data, remove any accessories or duplicates, and upload clothing images to a cloud storage. 

## Cleaning Instructions

To clean the data, follow these steps: 

1. **Navigate to the Scraper Folder**  
   Move into the `DataCleaning` directory (where this README.md is located at):

2. **Set up the Node Project**
   Make sure `package.json` is present in the directory, then run the following code in the command line:
   ```
   npm install
   ``` 
   This will install all the modules required by the scripts.

3. **Data Cleaning**
   3.1 Run `_clothingTypeExtraction.js` to see all the clothing types of all items:
   ```
   node _clothingTypeExtraction.js
   ```
   This will display all the clothing types in the terminal, make sure that the clothing type matches the value in `_removingExcess.js` after eliminating all accessory types.
   The logic of the function is simply extracting the last word of a clothing name and make it their type (ex: Oversized Sweatshirt -> Sweatshirt), in some cases it will extract words other than clothing types, please disregard them.  

   3.2 Making sure `_removingExcess.js` has all the correct clothing types, then run:
   ```
   node _removingExcess.js
   ```
   This will go through all the uncleaned data, remove accessory items, duplicated items, and apply slight modification on the features and rows.

   Modification:  
   1. Renaming feature `image` to `product` for clearer name choice on clothing images
   2. Modifying uniqlo product image urls by replacing query string sub13 to sub14. This is done because sub14 is usually the product image laying flat, while sub13 is for multiple products placed on the same screen. Due to the scraping logic, it was inevitable to scrap a few images with the sub13 query string in it.

   After running the script, a new json file named `cleaned_data.json` will be created inside `<project_root>/ClothingData/Cleaned`, this contains all the data scraped from all the sites and cleaned by the above scripts.

4. **Uploading Images To Google Cloud Platform Storage Bucket**
   Since we only have the url of all the images but not the actual file, we will need to download all the images. However, downloading all the images in the local storage would take up too much space and be hard to scale up. Thus we will utilize the cloud storage service provided by Google Cloud Platform and upload all the images there. These images will then be used for Machine Learning purpose, which will be done on Google Colab, a cloud based Jupyter Notebook Environment that allows you to run Machine Learning algorithms and has the access to GCP storage.  
   
   4.1 
   - Open the browser and head to `https://cloud.google.com/gcp`
   - Click on `Select a project` on the top left, and click on `New project` on the top right of the pop up window
   - Name the project as `ClothingProject`, and leave all other parameters as it is, then click `Create`
   - Reclick on `Select a project` and then select the project you have just created.  

   4.2
   - Click on the menu icon on the top left (looking like three bars), and select `Billing`
   - Follow the instruction to link a billing account  

   4.3
   - Open the menu again, hover onto `IAM & Admin`, then select `Service Accounts`
   - Click on `+ CREATE SERVICE ACCOUNT` at the top, follow the instructions to create a service account (name the account as `clothing-storage-access`, and leave all others as default)
   - Copy the service account email of the account you've just created, save it somewhere  
   - Click on the service account email, click on `KEYS` at the top, then click on `ADD KEY` to create a new key (select json format)
   - This will download you a service account key, rename the file to `clothingproject-key.json`

   4.4
   - Open the menu again, hover onto `Cloud Storage`, then select `Buckets`
   - Select `+ CREATE` to create a bucket, name the bucket as `product-image`, and leave all other fields as default
   - Then create another bucket and name it as `model-image`

   4.5
   - Click on each bucket and complete the following steps
   - Click on the `PERMISSIONS` tab, scroll down and find the `+ GRANT ACCESS` button
   - Click on the button, inside the `New Principals` text input, copy in the service account email you have just copied and stored elsewhere
   - In the `Roles` drop down box, select `Cloud Storage`, and then select `Storage Object Admin`
   - Now you have done setting up the cloud storage

   4.6
   - Before running the code, one last step needs to be done
   - Move the downloaded service account key, which is renamed to `clothingproject-key.json`, into the `DataCleaning` folder (where this README.md is located at)
   - Make sure that the variables inside `_uploadImagesToGCP.js` aligns with your google cloud items:
   ```
   const storage = new Storage({
         projectId: "clothingproject",
         keyFilename: "./clothingproject-key.json"
   });
   const productBucket = storage.bucket("product-image");
   const modelBucket = storage.bucket("model-image"); 
   ```
   If previously Google Cloud Platform has given your project a different id, or given your bucket a different name, modify the above variables to the correct values.

   4.7
   - Everything has been setup, run the following command to upload all the images onto GCP Storage Buckets
   ```
   node _uploadImagesToGCP.js
   ```
   After the code finishes running another json file named `image_uploaded.js` inside `<project_root>/ClothingData/Cleaned`
   This will not only contain the cleaned data, for each clothing object, two new attributes will be added: reference url to the gcp bucket image, one for the product, and one for the model.  
   Make sure that the images are correctly uploaded to your gcp bucket.
   A sample data file will also be placed at `<project_root>/ClothingData/Cleaned`.

   **Please proceed to the MLModels folder after completing all the steps above.**