# AutoCoder_GPT
Script for automatic programming with GPT4
In config.ini input your API key for GPT4 from OpenAI

At bottom of main.py set variables:
abstract - Your targets, why you need this code and what expect from solution. 
Example: "I want train my neural network and need dataset for it. Because my network it must predict frame next in 30 frames in video in canny egde format, so I need folders with image sequences. First folder must contain images with 16 tiles of sequential series of frames, ever next frame must be frame after 30 frames. Second folder must contain almost same images with same frames, but 16th tile in right bottom corner must be black square. Dataset must be loadable by hugging face datasets library. So folder structure must be in datasets fromat."

task - Exectly what code must do.
Example: "I need a code that load video in any format and convert it to array of frames, after that it must convert this frames to canny edge images, resize it to 256x256 pixels and save it to folder. After this it must make image 1024 x 1024 with 16 tiles of sequential series of frames (in tiles on image next frame it is next over 30 frames but every image start from next frame of previous image first frame) and save it to direcotry with name image_column . After this it must make another directory with almost same images with same names, but 16th tile in right bottom corner must be black square and result images must be saved to folder with name conditional_images. After this move folders to folders to be in hugging face datasets format. Move last 50 images to test folder. And 10 images to validation directory. Dataset must be loadable by hugging face datasets library. So directory structure must be in datasets fromat. Additionaly add one file with captions of every image and every caption must be \"earth rotating, image in canny edges, predict last frame\". Finally save dataset as Parquet file in hugging face datasets format and split by not more than 10mb files."

input_data - All what GPT need to resolve and test task.
Example: "video file url http://38.242.234.55/sample.mp4"

output_data - What you expect to get after code execution.
Example: "Directory with name ground_truth with images 1024 x 1024 with 16 tiles of sequential series of frames(any next frame here it is frame number + 30 ) and directory with name conditional_images with almost same images with same names, but 16th tile in right bottom corner must be black square. Json file with captions, and .parquet files"

