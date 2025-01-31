/*Iterate through all cleaned clothing data, upload the product image and model image to gcp bucket

    product image is from the "product" attribute of each json object
    model image is from the "model" attribute

    the product image file name will be "Type-Name-#", # is for clothes if they have the same type and name
    the model image file name will be "Type-Name-Model-#", 'Model' is not a placeholder, just a string

    store the product file name as an attribute in each json object, using the attribute name 'product-gcp'
    store the model file name as an attribute in each json object, using the attribute name 'model-gcp'

    the GCP project is named as 'ClothingProject'
    the product bucket is named as 'product-image-lyp'
    the model bucket is named as 'model-image-lyp'
*/

const fs = require("fs");

const path = require("path");

const { Storage } = require("@google-cloud/storage");

const axios = require("axios");

// Google Cloud Storage Configuration
const storage = new Storage({
    projectId: "clothingproject",
    keyFilename: "./clothingproject-key.json"
});
const productBucket = storage.bucket("product-image-lyp");
const modelBucket = storage.bucket("model-image-lyp");

const file = "../ClothingData/Cleaned/cleaned_data.json";
const outputFile = "../ClothingData/Cleaned/image_uploaded.json";

const uploadCount = new Map();

const USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
];

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function downloadImage(url, tempPath) {

    try {

        const userAgent = USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];

        const response = await axios({
            url,
            responseType: "stream",
            headers: {
                "User-Agent": userAgent,
            },
            timeout: 10000,
        });

        return new Promise((resolve, reject) => {

            const writer = fs.createWriteStream(tempPath);

            response.data.pipe(writer);

            writer.on("finish", async () => {

                await delay(1000 + Math.random() * 2000); // Wait 2-5 seconds before next request

                resolve(tempPath);

            });

            writer.on("error", reject);
        });

    } catch (error) {
        
        console.error(`Error downloading image from ${url}:`, error.response ? error.response.status : error);

        return null;
    }
}

async function uploadImage(imageUrl, bucket, destination) {

    const tempPath = path.join(__dirname, "temp_image.jpg");

    const downloadedImage = await downloadImage(imageUrl, tempPath);

    if (!downloadedImage) return null;

    try {

        // console.log(`Uploading ${destination} to bucket: ${bucket.name}...`);

        await bucket.upload(tempPath, {

            destination: destination,

            resumable: false,

        });

        fs.unlinkSync(tempPath); // Remove temp file after upload

        // console.log(`Upload complete: gs://${bucket.name}/${destination}`);

        return `gs://${bucket.name}/${destination}`;

    } catch (error) {

        console.error(`Error uploading ${imageUrl} to ${bucket.name}:`, error);

        return null;

    }
}

async function processFile(file) {

    try {

        const data = fs.readFileSync(file, "utf8");

        const clothings = JSON.parse(data);

        console.log(`Processing ${clothings.length} clothing items...`);

        let uploadedCount = 0;

        for (const clothing of clothings) {

            const key = `${clothing.type}-${clothing.name}`;

            uploadCount.set(key, (uploadCount.get(key) || 0) + 1);

            const count = uploadCount.get(key);

            if (clothing.product) {

                const productFileName = `${clothing.type}-${clothing.name}-${count}.jpg`;

                const productGCPUrl = await uploadImage(clothing.product, productBucket, productFileName);

                clothing["product-gcp"] = productGCPUrl;

            }

            if (clothing.model) {

                const modelFileName = `${clothing.type}-${clothing.name}-Model-${count}.jpg`;

                const modelGCPUrl = await uploadImage(clothing.model, modelBucket, modelFileName);

                clothing["model-gcp"] = modelGCPUrl;

            }

            uploadedCount++;

            console.log(`Progress: ${uploadedCount}/${clothings.length} items processed`);

        }

        fs.writeFileSync(outputFile, JSON.stringify(clothings, null, 4), "utf8");

        console.log(`Image upload complete! ${uploadedCount} items saved to ${outputFile}`);

    } catch (err) {

        console.error("Error processing file:", err);

    }

}

processFile(file);

