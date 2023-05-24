import multiprocessing
import time

import openai
import sys
from io import StringIO
from contextlib import redirect_stdout
import importlib.util
import tempfile
import os
import tiktoken
import traceback
import configparser


config = configparser.ConfigParser()
if os.path.exists("config.ini"):
    config.read('config.ini')
    print(config.sections())
    default = config['DEFAULT']
    openai.api_key = default['api_key']
    if len(openai.api_key) < 20:
        print("API key is not valid")
        k = input("Enter OpenAI API key: ")
        openai.api_key = k
    print(openai.api_key)
    model = default['model']
    iteration_limit = int(default['iteration_limit'])
    TOKEN_LIMIT = int(default['TOKEN_LIMIT'])
else:
    TOKEN_LIMIT = 8192
    k = input("Enter OpenAI API key: ")
    openai.api_key = k
    model = "gpt-4"
    iteration_limit = 5
    config['DEFAULT'] = {'openai_api_key': openai.api_key,
                         'model': model,
                         'iteration_limit': iteration_limit,
                         'TOKEN_LIMIT': TOKEN_LIMIT}




global_system_message = """At first in this case I use you as a code generator, tester and debugger. You see this messages but user not interact with you. 
So you must do all work by yourself in automatic mode. I make script that run your code and check output. If error occurred script catch it and resend it to you.
Your target is to make code that pass all tests and return correct answer.
You are coding machine, answer only runnable code, no commentaries, no explanation. 
Make as short as possible even if it is harder to understand. 
Please return only code, nothing more. Automated test script can be copied as is from you answer and be run without any preparations. 
If is need to install anything it must be installed inside code.
Define all variables and functions inside code. Do not use placeholders if possible.
Code must be executable as is. 
Very important: at the end of code must be this sequence #END"""



def count_tokens(promt, model="gpt-4"):
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(promt))
    return num_tokens

def split_prompt(prompt):
    parts = prompt.split(". ")
    splitted_prompts = []
    current_prompt = ""

    for part in parts:
        if count_tokens(current_prompt + part) >= int(0.7 * TOKEN_LIMIT):
            splitted_prompts.append(current_prompt.strip())
            current_prompt = ""

        current_prompt += part + ". "

    if current_prompt:
        splitted_prompts.append(current_prompt.strip())

    return splitted_prompts

def generate_code(prompt, system_message="", prev_assistant_message=""):
    finished_code = ""
    messages =[
        {"role": "system", "content": global_system_message},
        {"role": "system", "content": system_message},
        {"role": "assistant", "content": prev_assistant_message},
        {"role": "user", "content": prompt},
    ]
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print(messages)
    for i in range(15):
        try:

            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=0.5,
                max_tokens=2046,
                presence_penalty=0,
                frequency_penalty=0,
            )
            finished_code += response.choices[0].message["content"]
            code = response.choices[0].message["content"]
            if "#END" in code:
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print(finished_code)
                print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                finished_code = finished_code.split("#END")[0]
                print("Code generated successfully")
                return finished_code
            else:
                messages.append({"role": "assistant", "content": code})
            time.sleep(1)
        except openai.error.AuthenticationError:
            print("Authentication error, check your API key, it should be in config.ini file and be valid")
            if '"' in openai.api_key or "'" in openai.api_key:
                print("Your API key contains quotes, remove it")
            print("Example of API key: sk-1wY2BAuJgalyQot0Vhp3T36lb4FJ6R5Q9Kv3qbDehK7Ugm5t")
            print("Your key: " + openai.api_key)
            print("You can get API key here: https://beta.openai.com/account/api-keys")
            return None
        except Exception:
            traceback.print_exc()
            time.sleep(10)

    print("Code generation failed")
    return None

def generate_test_code(code):
    print("generating test code")
    system_message = """You must create automated test on Python for this Python code. 
    This test must testing is script work correctly. 
    Be aware that this code will be run in automated way, so you must not use any input() functions.
    Be aware code will be not process by human, so any variables must be defined inside code. No placeholders. No variables where user must put something.
    This test must check result of script work and it it not correct it must raise exception. 
    This test must be runnable as is.
    You can test on real data provided in input section. And use output section data as expected result.
    This test don't change anything in code, can only define input data and check result. Change code only if you need to define input data or fix error in code.
    If exception has rise this exception will be caught and reported as error to you in next iteration."""
    test_code = generate_code(code, system_message)
    return test_code

from multiprocessing import Process
import traceback


def run_code_in_process(code, test_code):
    try:
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        return_dict["finished"] = False
        p = Process(target=run_code, args=(code, test_code, return_dict))
        p.start()
        for i in range(1000):
            if return_dict["finished"]:
                return return_dict["result"]
            if p.is_alive():
                time.sleep(0.1)
            else:
                print("Process finished but fail")
                return return_dict["result"]
        return False, "Process not return anything but timeout. Probably code frozen. Or you use infinity loop.", None, None
    except Exception:
        traceback.print_exc()

def run_code(code, test_code, return_dict):
    return_dict["finished"] = False
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as temp:
        temp.write(code)
        temp_file_name = temp.name

    error_message = None
    trace = None
    try:
        spec = importlib.util.spec_from_file_location("generated_code", temp_file_name)
        generated_code_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generated_code_module)

        captured_output = StringIO()
        sys.stdout = captured_output
        exec(test_code, generated_code_module.__dict__)
        success = True
        output = captured_output.getvalue()
    except Exception as e:
        success = False
        error_message = str(e)
        trace = str(traceback.format_exc())
        output = None

    sys.stdout = sys.__stdout__
    os.remove(temp_file_name)
    return_dict["result"] = [success, error_message, trace, output]
    return_dict["finished"] = True
    return success, error_message, trace, output


def format_code(code):
    bash_code = ""
    if "```" in code:
        print(code)
        if "```bash" in code:
            start_bash = code.index("```bash") + len("```bash")
            end_bash = code.index("```", start_bash + 1)
            bash_code = code[start_bash:end_bash]
        if "```python" in code:
            start_python = code.index("```python") + len("```python")
            try:
                end_python = code.index("```", start_python + 1)
                python_code = code[start_python:end_python]
            except Exception:
                python_code = code[start_python:]
            code = python_code

    if bash_code != "":
        bash_code = bash_code.splitlines()
        code_ext = ""
        for line in bash_code:
            code_ext = code_ext + "\nos.system(\"" + line + "\")"
        code = "import os\n" + code_ext + code
    if "#END" in code:
        code = code.split("#END")[0]

    return code


def double_test_code(output, code_prompt, code, test_code):
    print("Code successfully passed tests")
    for i in range(iteration_limit):
        double_check_prompt = f"Your code return output: {output}\n\n Is this output what you predicted and correct? If yes answer to me only string [done] if not answer only sting [fail]. MOST IMPORTANT ONLY ANSWER [done] or [fail] !!! \n\nYour code:\n{code}\n\nAutomatic test code:\n{test_code}\n\n"
        double_check_response = generate_code(double_check_prompt, system_message=code_prompt, prev_assistant_message=code)
        if "[done]" in double_check_response.lower():
            print("Code is correct")
            return True
        elif "[fail]" in double_check_response.lower():
            print("Code is not correct")
            return False
        else:
            return False

def main_work(error_message, trace, code, test_code, output, code_prompt, success):
    for i in range(iteration_limit):
        iterations = i + 1
        fix_prompt = f"Your code return error: {error_message}\n\n Traceback:{trace} \n\nYour code:\n{code}\n\nAutomatic test code:\n{test_code}\n\nYou must return only fixed code."
        if success:
            if double_test_code(output, code_prompt, code, test_code):
                print("Code is correct")
                with open("generated_code.py", "w") as output_file:
                    output_file.write(code)
                print("Sucessfully saved result to  generated_code.py. Complited in %i iterations" % iterations)
                print("Human you must check code and run it in your environment. "
                      "Is all ok? If yes press enter or input what is problem.")
                a = input("It is ok? Problem is:")
                if a == "":
                    print("All is ok. Work is done.")
                    return True
                else:
                    fix_prompt = f": {a}\n\n Your code:\n{code}\n\nAutomatic test code:" \
                                 f"\n{test_code}\n\nYou must return only fixed code."
                    code = generate_code(fix_prompt, system_message=code_prompt, prev_assistant_message=code)
                    success, error_message, trace, output = run_code_in_process(code, test_code)
                continue
            else:
                print(f"Double test failed, try code interation {i}")
                print(f"Problem in code, output: {output}")
                print(f"Problem in code, trace: {trace}")
                fix_prompt = f"Your code return wrong output: {output}\n\n Traceback:{trace} \n\nYour code:\n{code}\n\nAutomatic test code:\n{test_code}\n\nYou must return only fixed code."
        print("Try code interation %i" % i)
        print(f"Problem in code, output: {output}")
        print(f"Problem in code, trace: {trace}")
        code = generate_code(fix_prompt, system_message=code_prompt, prev_assistant_message=code)
        success, error_message, trace, output = run_code_in_process(code, test_code)
    return False


if __name__ == "__main__":
    print("started")
    first_prompt_template = """
    Abstract: {abstract}
    Your task is: {task}
    Your code have this input data (input section): {input_data}
    Result of code running must be (output section): {output_data}
    """
    # abstract = input("Abstract part: ")
    # task = input("Task part: ")
    # input_data = input("Input data: ")
    # output_data = input("Output data: ")
    abstract = "I want train my neural network and need dataset for it. Because my network it must predict frame next in 30 frames in video in canny egde format, so I need folders with image sequences. First folder must contain images with 16 tiles of sequential series of frames, ever next frame must be frame after 30 frames. Second folder must contain almost same images with same frames, but 16th tile in right bottom corner must be black square. Dataset must be loadable by hugging face datasets library. So folder structure must be in datasets fromat."
    task = "I need a code that load video in any format and convert it to array of frames, after that it must convert this frames to canny edge images, resize it to 256x256 pixels and save it to folder. After this it must make image 1024 x 1024 with 16 tiles of sequential series of frames (in tiles on image next frame it is next over 30 frames but every image start from next frame of previous image first frame) and save it to folder with name image_column . After this it must make another folder with almost same images with same names, but 16th tile in right bottom corner must be black square and result images must be saved to folder with name conditional_images. After this move folders to folders to be in hugging face datasets format. Move last 50 images to test folder. And 10 images to validation folder. Dataset must be loadable by hugging face datasets library. So folder structure must be in datasets fromat. Additionaly add one file with captions of every image and every caption must be \"earth rotating, image in canny edges, predict last frame\". Finally save dataset as Parquet file in hugging face datasets format and split by not more than 10mb files."
    input_data = "video file url http://38.242.234.55/sample.mp4"
    output_data = "Dataset must be uploaded to hugging face by datasets library. So folder structure must be in hugging face datasets fromat. Folder with name ground_truth with images 1024 x 1024 with 16 tiles of sequential series of frames(any next frame here it is frame number + 30 ) and folder with name conditional_images with almost same images with same names, but 16th tile in right bottom corner must be black square. Json file with captions, and .parquet files"

    code_prompt = first_prompt_template.format(abstract=abstract, task=task, input_data=input_data, output_data=output_data)

    code = generate_code(code_prompt, "Write code that solve this task.")
    code = format_code(code)
    print("code formatted")
    test_code = generate_test_code(code)
    print("test code generated")
    success, error_message, trace, output = run_code_in_process(code, test_code)
    print("success: ", success)
    print("error_message: ", error_message)
    print("trace: ", trace)
    generation_result = main_work(error_message, trace, code, test_code, output, code_prompt, success)
    if not generation_result:
        print("The code tests failed and iterations over. Please fix your task.")