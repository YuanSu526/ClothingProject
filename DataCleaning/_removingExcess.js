/*Cleaning data by:
    only keeping the items containing one of the word in below 
    removing duplicated data
    removing data without images
    removing the color_variations column
*/

const fs = require("fs");
const path = "../ClothingData/Uncleaned/";
const outputFile = "../ClothingData/Cleaned/cleaned_data.json";

// List of files to process
const files = ["uniqlo_data.json", "massimo_data.json", "cos_data.json", "zara_data.json"];

// Clothing types to keep
const contains = new Set([
    'BLAZER', 'SHIRT', 'JACKET', 'SWEATER', 'TROUSERS', 'CARDIGAN',
    'JEANS', 'GILET', 'COAT', 'OVERSHIRT', 'T-SHIRT', 'VEST', 'JUMPER', 'PANTS', 
    'SWEATSHIRT', 'SHORTS', 'LEGGINGS', 'PARKA', 'BLOUSON', 'HOODIE', 'SWEATPANTS', 
    'JOGGERS', 'OVERCOAT', 'T-SHIRTS', 'CHINOS', 'POLO', 'TOP', 'OVERALLS'
]);

// Map to store unique items (by name and color)
const uniqueItems = new Map();

// Function to process a single file
function processFile(file) {

    return new Promise((resolve, reject) => {

        fs.readFile(path + file, "utf8", (err, data) => {

            if (err) {

                console.error(`Error reading ${file}:`, err);

                reject(err);

                return;

            }

            try {

                const clothings = JSON.parse(data);
                
                clothings.forEach(clothing => {

                    clothing.name = clothing.name.toUpperCase();
                    
                    let type = clothing.name.split(" ").slice(-1)[0];

                    if (!contains.has(type)) return;

                    if (!clothing.image || clothing.image.trim() === "") return;

                    delete clothing.color_variations;

                    clothing.type = type;

                    clothing.product = clothing.image.replace("sub13", "sub14");

                    delete clothing.image;
                    
                    const uniqueKey = `${clothing.name}-${clothing.color}`;

                    if (!uniqueItems.has(uniqueKey)) {

                        uniqueItems.set(uniqueKey, clothing);

                    }

                });

                console.log(`Processed ${file}`);

                resolve();

            } catch (parseError) {

                console.error(`Error parsing ${file}:`, parseError);

                reject(parseError);

            }

        });

    });

}

Promise.all(files.map(file => processFile(file))).then(() => {

    const cleanedData = [...uniqueItems.values()];

    fs.writeFileSync(outputFile, JSON.stringify(cleanedData, null, 4), "utf8");

    console.log(`Cleaning complete! Saved ${cleanedData.length} items to ${outputFile}`);

}).catch(err => {

    console.error("Error processing files:", err);

});