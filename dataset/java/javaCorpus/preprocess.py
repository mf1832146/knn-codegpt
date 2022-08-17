# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import argparse
import re
import javalang
import json
from javalang.tokenizer import *
from tqdm import tqdm

from dataset.java.utils import deal_with_java


def get_value_save(obj, key):
    if key in obj:
        return obj[key]
    else:
        return None


def preprocess(args, file_name, file_type):
    contents = open(os.path.join(args.base_dir, file_name)).readlines()
    wf = open(os.path.join(args.output_dir, f"{file_type}.txt"), 'w')

    for content in tqdm(contents, desc='deal with file ' + file_type + '...'):
        content = json.loads(content)
        code = get_value_save(content, 'code')
        try:
            code_tokens, code_types = deal_with_java(code)
        except Exception:
            continue
        if len(code_tokens) == 0:
            continue
        data = ['<s>'] + code_tokens + ["</s>"]
        data_type = [-1] + code_types + [-1]
        content['code'] = data
        content['token_type'] = data_type
        wf.write(json.dumps(content) + "\n")

    wf.flush()
    wf.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_dir", default="token_completion", type=str,
                        help="The downloaded data path")
    parser.add_argument("--output_dir", default="token_completion", type=str,
                        help="The output directory")
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    preprocess(args, file_name="source_train.txt", file_type="train")
    preprocess(args, file_name="source_valid.txt", file_type="dev")
    preprocess(args, file_name="source_test.txt", file_type="test")

if __name__ == "__main__":
    main()