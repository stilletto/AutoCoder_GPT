# Automated Programming Script with GPT-4

This script leverages GPT-4 to automate specific programming tasks. To get started, you'll need to provide your GPT-4 API key from OpenAI in the `config.ini` file.

## Setting up `main.py`

At the bottom of `main.py`, you'll need to define several variables to configure the script according to your needs:

### `abstract`
**Purpose and Expected Outcome**  
Detail your objectives and what you hope to achieve with this script.  
**Example**:  
"I aim to train my neural network and require a dataset for this purpose. The network should predict the next frame in a video sequence, specifically 30 frames ahead, and process these in a Canny edge format. Consequently, I need two folders containing image sequences. The first folder should have images comprising 16 tiles of sequential frame series, with each subsequent frame being 30 frames apart. The second folder should closely mirror the first, but with a black square in the bottom right tile. The dataset should adhere to Hugging Face datasets' structure for compatibility."

### `task`
**Specific Requirements**  
Describe in detail what the script needs to accomplish.  
**Example**:  
"The code should load a video in any format, converting it to a frame array, transitioning these into Canny edge images, resizing them to 256x256 pixels, and storing them in a specified folder. It should then assemble an image of 1024x1024 pixels with 16 tiles of sequential frames, spaced 30 frames apart, saving this to a directory named `image_column`. A similar process should create a second directory of images (`conditional_images`), but with a black square in the 16th tile. The directories should be structured according to the Hugging Face datasets format. Move the last 50 images to a `test` folder, and 10 images to a `validation` directory. Additionally, include a file with captions for each image, labeled as 'earth rotating, image in Canny edges, predict last frame'. Finally, the dataset should be saved as Parquet files, split into chunks no larger than 10MB, formatted for Hugging Face datasets."

### `input_data`
**Required Input**  
Specify all necessary inputs for the task.  
**Example**:  
"Video file URL: http://38.242.234.55/sample.mp4"

### `output_data`
**Expected Output**  
Define what the script is expected to generate upon execution.  
**Example**:  
"A directory named `ground_truth` containing images of 1024x1024 pixels with 16 sequential frame tiles (each subsequent frame spaced by 30 frames), and a `conditional_images` directory with similar images, except the 16th tile in the bottom right corner must be a black square. Additionally, a JSON file with captions and Parquet files should be produced."

By properly configuring these variables, you ensure the script understands your project's needs and executes the task as required.

