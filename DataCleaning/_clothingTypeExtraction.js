/*Help examine all the clothing types by looking at the last word of each clothing name*/

const fs = require("fs");
const path = "../ClothingData/Uncleaned/";

const files = ["uniqlo_data.json", "massimo_data.json", "cos_data.json", "zara_data.json"];

const clothingTypeMap = new Map();

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

                    let name = clothing.name.toUpperCase();

                    let type = name.split(" ").slice(-1)[0];

                    clothingTypeMap.set(type, (clothingTypeMap.get(type) || 0) + 1);
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

    console.log("\nUnique Clothing Types:");

    console.table([...clothingTypeMap.keys()]);

}).catch(err => {

    console.error("Error processing files:", err);

});
