# Copyright (c) Microsoft Corporation. 
# Licensed under the MIT license.
import os
import logging
import argparse
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def read_true_gts(data_dir, file_type):
    true_gts = []
    types = []
    data = open(os.path.join(data_dir, f"{file_type}.txt")).readlines()
    for s in data:
        s = json.loads(s)
        code = s['code']
        code_type = s['token_type']

        types.append(code_type)
        true_gts.append(code)
    return true_gts, types


def main():
    parser = argparse.ArgumentParser(description='Evaluate leaderboard predictions for code completion (token level).')
    parser.add_argument('--data_dir', '-a', required=True, help="filename of the labels, in txt format.")
    parser.add_argument('--predictions', '-p', required=True, help="filename of the leaderboard predictions, in txt format.")
    args = parser.parse_args()

    preds = open(args.predictions, "r").readlines()
    gts, types = read_true_gts(args.data_dir, 'test')

    total = 0
    correct = 0.0
    code_type_dict = {}
    code_type_correct = {}
    i = 0
    for pred, gt, code_type in zip(preds, gts, types):
        i+=1
        pred = pred.split()

        if len(pred) != len(gt):
            print('skip')
            continue
        assert len(pred) == len(gt), f"Sequence length of prediction and answer are not equal, \n{pred}: \n{gt}\n{i-1}"
        assert len(code_type) == len(gt), f"Code type length mush be equal to the ground truth. \n{code_type}\n: {gt}\n{i-1}"

        for j, (x, y, z) in enumerate(zip(pred, gt, code_type)):
            if y not in ["<s>", "</s>", "<EOL>", "<pad>"]:
                total += 1
                if z not in code_type_dict:
                    code_type_dict[z] = 0
                    code_type_correct[z] = 0
                code_type_dict[z] += 1
                if x == y:
                    correct += 1
                    code_type_correct[z] += 1

    code_type_correct = {k: round(v / code_type_dict[k] * 100, 2)for k, v in code_type_correct.items()}
    code_type_dict = {k: round(v/total*100, 2) for k,v in code_type_dict.items()}

    logger.info(f"Total {total} tokens, accuracy: {round(correct/total*100, 2)}")
    logger.info(f"Percent code types: " + json.dumps(code_type_dict))
    logger.info(f"Code type accuracy: " + json.dumps(code_type_correct))


if __name__ == "__main__":
    main()