# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
from __future__ import absolute_import, division, print_function

import argparse
import glob
import logging
import os
import pickle
import random
import re
import gc
import shutil
import json

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset, SequentialSampler, RandomSampler,TensorDataset
from torch.utils.data.distributed import DistributedSampler

from transformers import (WEIGHTS_NAME, AdamW, get_linear_schedule_with_warmup,
                          BertConfig, BertForMaskedLM, BertTokenizer,
                          GPT2Config, GPT2LMHeadModel, GPT2Tokenizer,
                          OpenAIGPTConfig, OpenAIGPTLMHeadModel, OpenAIGPTTokenizer,
                          RobertaConfig, RobertaForMaskedLM, RobertaTokenizer,
                          DistilBertConfig, DistilBertForMaskedLM, DistilBertTokenizer)

class TextDataset(Dataset):
    def __init__(self, tokenizer, args, logger, file_type='train', block_size=1024):
        if args.local_rank==-1:
            local_rank=0
            world_size=1
        else:
            local_rank=args.local_rank
            world_size=torch.distributed.get_world_size()

        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
        cached_file = os.path.join(args.output_dir, file_type+"_langs_%s"%(args.langs)+"_blocksize_%d"%(block_size)+"_wordsize_%d"%(world_size)+"_rank_%d"%(local_rank))
        if os.path.exists(cached_file) and not args.overwrite_cache:
            if file_type == 'train':
                logger.warning("Loading features from cached file %s", cached_file)
            with open(cached_file, 'rb') as handle:
                self.inputs = pickle.load(handle)

        else:
            self.inputs = []
            if args.langs == 'all':
                langs = os.listdir(args.data_dir)
            else:
                langs = [args.langs]

            data=[]
            for lang in langs:
                datafile = os.path.join(args.data_dir, lang, file_type+'.pkl')
                if file_type == 'train':
                    logger.warning("Creating features from dataset file at %s", datafile)
                # with open(datafile) as f:
                #     data.extend([json.loads(x)['code'] for idx,x in enumerate(f.readlines()) if idx%world_size==local_rank])
                dataset = pickle.load(open(datafile, 'rb'))
                data.extend(['<s> '+' '.join(x['function'].split())+' </s>' for idx,x in enumerate(dataset) if idx%world_size==local_rank])

            # random.shuffle(data)
            data = data
            length = len(data)
            logger.warning("Data size: %d"%(length))
            input_ids = []
            for idx,x in enumerate(data):
                try:
                    input_ids.extend(tokenizer.encode(x))
                except Exception:
                    pass
                if idx % (length//10) == 0:
                    percent = idx / (length//10) * 10
                    logger.warning("Rank %d, load %d"%(local_rank, percent))
            del data
            gc.collect()

            length = len(input_ids)
            for i in range(0, length-block_size, block_size):
                self.inputs.append(input_ids[i : i + block_size])            
            del input_ids
            gc.collect()

            if file_type == 'train':
                logger.warning("Rank %d Training %d token, %d samples"%(local_rank, length, len(self.inputs)))
                logger.warning("Saving features into cached file %s", cached_file)
            with open(cached_file, 'wb') as handle:
                pickle.dump(self.inputs, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def __len__(self):
        return len(self.inputs)

    def __getitem__(self, item):
        return torch.tensor(self.inputs[item])


def get_value_save(obj, key):
    if key in obj:
        return obj[key]
    else:
        return None


class finetuneDataset(Dataset):
    def __init__(self, tokenizer, args, logger, file_type='train', block_size=1024):
        if args.local_rank==-1:
            local_rank=0
            world_size=1
        else:
            local_rank=args.local_rank
            world_size=torch.distributed.get_world_size()

        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
        cached_file = os.path.join(args.output_dir, file_type+"_blocksize_%d"%(block_size)+"_wordsize_%d"%(world_size)+"_rank_%d"%(local_rank))
        if os.path.exists(cached_file) and not args.overwrite_cache:
            if file_type == 'train':
                logger.warning("Loading features from cached file %s", cached_file)
            with open(cached_file, 'rb') as handle:
                self.inputs = pickle.load(handle)

        else:
            self.inputs = []

            datafile = os.path.join(args.data_dir, f"{file_type}.txt")
            if file_type == 'train':
                logger.warning("Creating features from dataset file at %s", datafile)
            with open(datafile) as f:
                data = f.readlines()

            length = len(data)
            logger.info("Data size: %d"%(length))
            input_ids = []
            for idx,x in enumerate(data):
                x = json.loads(x)
                #before_code = get_value_save(x, 'before_code')
                #after_code = get_value_save(x, 'after_code')
                #code = ""
                #if before_code is not None:
                #    code += before_code + " "
                #code += after_code
                code = get_value_save(x, 'code')
                #project_name = get_value_save(x, 'project')
                x = code

                if x.startswith("<s>") and x.endswith("</s>"):
                    pass
                else:
                    x = "<s> " + x + " </s>"
                try:
                    input_ids.extend(tokenizer.encode(x))
                except Exception:
                    pass
                if idx % (length//10) == 0:
                    percent = idx / (length//10) * 10
                    logger.warning("Rank %d, load %d"%(local_rank, percent))
            del data
            gc.collect()

            length = len(input_ids) // world_size
            logger.info(f"tokens: {length*world_size}")
            input_ids = input_ids[local_rank*length: (local_rank+1)*length]

            for i in range(0, length-block_size, block_size):
                self.inputs.append(input_ids[i : i + block_size])            
            del input_ids
            gc.collect()

            if file_type == 'train':
                logger.warning("Rank %d Training %d token, %d samples"%(local_rank, length, len(self.inputs)))
                logger.warning("Saving features into cached file %s", cached_file)
            with open(cached_file, 'wb') as handle:
                pickle.dump(self.inputs, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def __len__(self):
        return len(self.inputs)

    def __getitem__(self, item):
        return torch.tensor(self.inputs[item])


class EvalDataset(Dataset):
    def __init__(self, tokenizer, args, logger, file_type='train', block_size=1024):
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
        cached_file = os.path.join(args.output_dir, file_type+"_blocksize_%d"%(block_size))
        if os.path.exists(cached_file) and not args.overwrite_cache:
            with open(cached_file, 'rb') as handle:
                load_data = pickle.load(handle)

                self.inputs = load_data['input_ids']
                self.input_types = load_data['input_types']
                self.sample2proj = load_data['sample2proj']
                self.file2sample = load_data['file2sample']
                self.sample2file = load_data['sample2file']

        else:
            self.inputs = []
            proj_list = []
            self.proj2sample = {}
            self.sample2proj = {}
            self.sample2file = {}
            self.file2sample = {}
            self.input_types = []

            datafile = os.path.join(args.data_dir, f"{file_type}.txt")
            with open(datafile) as f:
                data = f.readlines()

            length = len(data)
            logger.info("Data size: %d"%(length))
            input_ids = []

            for idx,x in enumerate(data):
                x = json.loads(x)
                #before_code = get_value_save(x, 'before_code')
                #after_code = get_value_save(x, 'after_code')
                #code = ""
                #if before_code is not None:
                #    code += before_code + " "
                #code += after_code
                code = get_value_save(x, 'code')
                code_type = get_value_save(x, 'token_type')
                project_name = get_value_save(x, 'project')
                if project_name not in proj_list:
                    proj_list.append(project_name)
                proj_index = proj_list.index(project_name)

                if proj_index not in self.proj2sample:
                    self.proj2sample[proj_index] = []

                if idx not in self.file2sample:
                    self.file2sample[idx] = []

                try:
                    code_token_ids = []
                    code_type_ids = []

                    for i, code_token in enumerate(code):
                        if i > 0:
                            code_token = ' ' + code_token  # 补上前缀
                        token_id = tokenizer.encode(code_token)
                        code_token_ids.extend(token_id)
                        code_type_ids.extend([code_type[i]] * len(token_id))

                    assert len(code_token_ids) == len(code_type_ids)

                    i = 0
                    while i < len(code_token_ids):
                        sample = code_token_ids[i: i + block_size]
                        sample_type = code_type_ids[i: i+block_size]
                        if len(sample) == block_size:
                            for j in range(block_size):
                                if tokenizer.convert_ids_to_tokens(sample[block_size - 1 - j])[
                                    0] == '\u0120' or tokenizer.convert_ids_to_tokens(
                                    sample[block_size - 1 - j]).startswith("<NUM_LIT"):
                                    break
                                if sample[block_size - 1 - j] in [tokenizer.bos_token_id, tokenizer.eos_token_id,
                                                                  tokenizer.sep_token_id]:
                                    if sample[block_size - 1 - j] != tokenizer.bos_token_id:
                                        j -= 1
                                    break
                            if j == block_size - 1:
                                print(tokenizer.decode(sample))
                                exit()
                            sample = sample[: block_size - 1 - j]
                            sample_type = sample_type[: block_size - 1 - j]
                            i += len(sample)
                            pad_len = block_size - len(sample)
                            sample += [tokenizer.pad_token_id] * pad_len
                            sample_type += [tokenizer.pad_token_id] * pad_len
                            input_ids.append(sample)
                            self.input_types.append(sample_type)

                            cur_index = len(input_ids) - 1
                            self.sample2proj[cur_index] = proj_index
                            self.proj2sample[proj_index].append(cur_index)

                            self.file2sample[idx].append(cur_index)
                            self.sample2file[cur_index] = idx
                        else:
                            pad_len = block_size - len(sample)
                            sample += [tokenizer.pad_token_id] * pad_len
                            sample_type += [tokenizer.pad_token_id] * pad_len
                            input_ids.append(sample)
                            self.input_types.append(sample_type)

                            cur_index = len(input_ids) - 1
                            self.sample2proj[cur_index] = proj_index
                            self.proj2sample[proj_index].append(cur_index)

                            self.file2sample[idx].append(cur_index)
                            self.sample2file[cur_index] = idx
                            break
                except Exception as e:
                    print(e)
                    raise e
                if idx % (length // 10) == 0:
                    percent = idx / (length // 10) * 10
                    logger.warning("load %d" % (percent))

            del data
            gc.collect()

            self.inputs = input_ids

            save_file = {
                'input_ids': input_ids,
                'input_types': self.input_types,
                'sample2proj': self.sample2proj,
                'proj2sample': self.proj2sample,
                'file2sample': self.file2sample,
                'sample2file': self.sample2file
            }

            with open(cached_file, 'wb') as handle:
                pickle.dump(save_file, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def __len__(self):
        return len(self.inputs)

    def __getitem__(self, item):
        proj_meta = torch.LongTensor([self.sample2proj[item], self.sample2file[item]])
        return torch.tensor(self.inputs[item]), torch.IntTensor(self.input_types[item]), proj_meta


class EvalDomainDataset(Dataset):
    def __init__(self, tokenizer, args, logger, file_type='train', block_size=1024):
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
        cached_file = os.path.join(args.output_dir, file_type+"_blocksize_%d"%(block_size))
        self.file_type = file_type
        if os.path.exists(cached_file) and not args.overwrite_cache:
            with open(cached_file, 'rb') as handle:
                load_data = pickle.load(handle)

                self.inputs = load_data['input_ids']
                self.input_types = load_data['input_types']

        else:
            self.inputs = []
            input_types = []

            datafile = os.path.join(args.data_dir, f"{file_type}.txt")
            with open(datafile) as f:
                data = f.readlines()

            length = len(data)
            logger.info("Data size: %d"%(length))
            input_ids = []

            for idx,x in enumerate(data):
                x = json.loads(x)
                code = get_value_save(x, 'code')
                code_type = get_value_save(x, 'token_type')

                try:
                    code_token_ids = []
                    code_type_ids = []

                    for i, code_token in enumerate(code):
                        if i > 0:
                            code_token = ' ' + code_token  # 补上前缀
                        token_id = tokenizer.encode(code_token)
                        code_token_ids.extend(token_id)
                        code_type_ids.extend([code_type[i]] * len(token_id))

                    assert len(code_token_ids) == len(code_type_ids)

                    i = 0
                    while i < len(code_token_ids):
                        sample = code_token_ids[i: i + block_size]
                        sample_type = code_type_ids[i: i+block_size]
                        if len(sample) == block_size:
                            for j in range(block_size):
                                if tokenizer.convert_ids_to_tokens(sample[block_size - 1 - j])[
                                    0] == '\u0120' or tokenizer.convert_ids_to_tokens(
                                    sample[block_size - 1 - j]).startswith("<NUM_LIT"):
                                    break
                                if sample[block_size - 1 - j] in [tokenizer.bos_token_id, tokenizer.eos_token_id,
                                                                  tokenizer.sep_token_id]:
                                    if sample[block_size - 1 - j] != tokenizer.bos_token_id:
                                        j -= 1
                                    break
                            if j == block_size - 1:
                                print(tokenizer.decode(sample))
                                exit()
                            sample = sample[: block_size - 1 - j]
                            sample_type = sample_type[: block_size - 1 - j]
                            i += len(sample)
                            pad_len = block_size - len(sample)
                            sample += [tokenizer.pad_token_id] * pad_len
                            sample_type += [tokenizer.pad_token_id] * pad_len
                            input_ids.append(sample)
                            input_types.append(sample_type)
                        else:
                            pad_len = block_size - len(sample)
                            sample += [tokenizer.pad_token_id] * pad_len
                            sample_type += [tokenizer.pad_token_id] * pad_len
                            input_ids.append(sample)
                            input_types.append(sample_type)
                            break
                except Exception as e:
                    print(e)
                    raise e
                if idx % (length // 10) == 0:
                    percent = idx / (length // 10) * 10
                    logger.warning("load %d" % (percent))

            del data
            gc.collect()

            self.inputs = input_ids
            self.input_types = input_types
            save_file = {
                'input_ids': input_ids,
                'input_types': input_types
            }

            with open(cached_file, 'wb') as handle:
                pickle.dump(save_file, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def __len__(self):
        return len(self.inputs)

    def __getitem__(self, item):
        return torch.tensor(self.inputs[item]), torch.IntTensor(self.input_types[item])



class lineDataset(Dataset):
    def __init__(self, tokenizer, args, logger, file_type='test', block_size=924):
        datafile = os.path.join(args.data_dir, f"{file_type}.json")
        with open(datafile) as f:
            datas = f.readlines()

        length = len(datas)
        logger.info("Data size: %d"%(length))
        self.inputs = []
        self.gts = []
        for data in datas:
            data = json.loads(data.strip())
            self.inputs.append(tokenizer.encode(data["input"])[-block_size:])
            self.gts.append(data["gt"])

    def __len__(self):
        return len(self.inputs)

    def __getitem__(self, item):
        return torch.tensor(self.inputs[item]), self.gts[item]
