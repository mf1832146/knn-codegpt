import os.path

import javalang


def parse_directory(dir_path):
    if not os.path.exists(dir_path):
        exit_with_message(f'Could not find directory: {dir_path}')

    walk = os.walk(dir_path)
    for sub_dir, _, files in walk:
        for filename in files:
            path = os.path.join(sub_dir, filename)
            if filename.endswith('.java'):
                pass


def parse_file(path):
    code = ''
    with open(path, 'r', encoding='utf-8') as file:
        code = file.read()

    try:
        tokens = list(javalang.tokenizer.tokenize(code))






def exit_with_message(message):
    print(f"{message} Exiting...")
    exit(1)