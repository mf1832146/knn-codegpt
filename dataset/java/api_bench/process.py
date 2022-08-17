import argparse
import json
import os.path

import javalang
from tqdm import tqdm

from ..utils import deal_with_java


def parse_directory(dir_path):
    if not os.path.exists(dir_path):
        exit_with_message(f'Could not find directory: {dir_path}')

    walk = os.walk(dir_path)
    contents = []
    for sub_dir, _, files in walk:
        for filename in files:
            path = os.path.join(sub_dir, filename)
            if filename.endswith('.java'):
                file_content = parse_file(path)
                if file_content is not None:
                    contents.append(file_content)
                    if len(contents) % 100 == 0:
                        print(len(contents), ' are done!')

    return contents


def write_to_file(contents, file_type):
    wf = open(os.path.join(args.output_dir, f"{file_type}.txt"), 'w')
    for content in tqdm(contents, desc='write to file ' + file_type + '...'):
        wf.write(json.dumps(content) + "\n")

    wf.flush()
    wf.close()


def parse_file(path):
    code = ''
    with open(path, 'r', encoding='utf-8') as file:
        code = file.read()

    content = {}
    try:
        code_tokens, code_types = deal_with_java(code)

        data = ['<s>'] + code_tokens + ["</s>"]
        data_type = [-1] + code_types + [-1]
        content['code'] = data
        content['token_type'] = data_type

        return content
    except Exception:
        return None


def exit_with_message(message):
    print(f"{message} Exiting...")
    exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="", type=str,
                        help="domain dataset dir")
    parser.add_argument("--output_dir", default="token_completion", type=str,
                        help="The output directory")
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # need to split train and dev dataset!
    for file_type in ['Training', 'Testing']:
        data_dir = os.path.join(args.data_dir, file_type)
        results = parse_directory(data_dir)

        if file_type == 'Training':
            dev_len = len(results) // 10
            train_len = len(results) - dev_len
            dev_results = results[-dev_len:]
            train_results = results[: train_len]

            write_to_file(train_results, 'train')
            write_to_file(dev_results, 'dev')

        else:
            write_to_file(results, 'test')


