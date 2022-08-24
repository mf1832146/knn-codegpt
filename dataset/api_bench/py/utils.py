from numbers import Number
import codeprep.api.text as cp
import re
from codeprep.tokens.containers import SplitContainer, StringLiteral, TextContainer
from codeprep.tokens.whitespace import NewLine, Tab
from codeprep.tokens.word import KeyWord, Semicolon, OpeningCurlyBracket, OpeningBracket, ClosingBracket, Operator, \
    ClosingCurlyBracket

import json
lits = json.load(open("literals.json"))

keywords = [KeyWord.__name__]

punctuations = [Semicolon.__name__, OpeningCurlyBracket.__name__,
                OpeningBracket.__name__, ClosingBracket.__name__,
                ClosingCurlyBracket.__name__]

py_punct = [NewLine.__name__, Tab.__name__]

operators = [Operator.__name__]

identifiers = [SplitContainer.__name__]

literals = [StringLiteral.__name__, Number.__name__]


def process_string(token, special_chars={" ": "U+0020", ",": "U+002C"}):
    str_quote_options = ["'''", '"""', "'", '"']
    start_quote = ""
    end_quote = ""
    qualifier_regex = r"^[a-z]+"
    qualifier_match = re.search(qualifier_regex, token)
    # string qualifiers like 'r' for regex, 'f' for formatted string, 'b' for bytes, 'u' for unicode, etc (or combination of them)
    qualifier = "" if not qualifier_match else qualifier_match[0]
    # token string without qualifiers
    token_string = re.sub(qualifier_regex, "", token)
    # string literal without quotes
    str_lit = token_string
    for q in str_quote_options:
        if token_string.startswith(q):
            start_quote = q
            str_lit = str_lit[len(q) :]
            if token_string.endswith(q):
                end_quote = q
                str_lit = str_lit[: -len(q)]
            break
    use_char = False
    if len(str_lit) == 1 and start_quote == "'":
        use_char = True
    for sc in special_chars:
        str_lit = str_lit.replace(sc, special_chars[sc])
    if not use_char:
        ret = (
            f"{qualifier}{start_quote}<STR_LIT:{str_lit}>{end_quote}"
            if str_lit in lits['str']
            else f"{qualifier}{start_quote}<STR_LIT>{end_quote}"
        )
    else:
        ret = (
            f"{qualifier}{start_quote}<CHAR_LIT:{str_lit}>{end_quote}"
            if str_lit in lits['char']
            else f"{qualifier}{start_quote}<CHAR_LIT>{end_quote}"
        )
    return ret


def deal_with_code(code, lang):
    no_spaces = True if lang == 'java' else False
    tokens, metadata = cp.nosplit(code,
                                  extension=lang,
                                  no_spaces=no_spaces,
                                  no_unicode=True,
                                  no_com=True,
                                  full_strings=True,
                                  max_str_length=15,
                                  return_metadata=True)

    token_types = list(map(lambda x: x.__name__, metadata.token_types))

    tmp_str = []
    processed_tokens = []
    processed_types = []
    code_token_len = len(tokens)
    for i, (token, token_type) in enumerate(zip(tokens, token_types)):
        if token == '<comment>':
            continue
        # deal with string
        if token_type == StringLiteral.__name__:
            tmp_str.append(token)
            if i + 1 < code_token_len and token_types[i + 1] == StringLiteral.__name__:
                continue
            else:
                string = ''.join(tmp_str)
                new_str = process_string(string)
                processed_tokens.append(new_str)
                processed_types.append('literals')
                continue

        # deal with number
        if token_type == Number.__name__:
            if token in lits['num']:
                token = f"<NUM_LIT:{token}>"
            else:
                token = "<NUM_LIT>"

        # for python
        if token_type in py_punct:
            token = '<EOL>'
            if i - 1 >= 0 and token_types[i - 1] in py_punct:
                continue

        if token_type in keywords:
            token_type = 'keyword'
        elif token_type in punctuations:
            token_type = 'punctuation'
        elif token_type in operators:
            token_type = 'operator'
        elif token_type in identifiers:
            token_type = 'identifier'
        elif token_type in literals:
            token_type = 'literals'
        elif token_type in py_punct:
            token_type = 'punctuation'
        else:
            token_type = 'unknown'

        if ' ' in token:
            sub_token = token.split()
            processed_tokens.extend(sub_token)
            processed_types.extend([token_type] * len(sub_token))
        else:
            processed_tokens.append(token)
            processed_types.append(token_type)

    if processed_tokens[0] == '<EOL>':
        processed_tokens = processed_tokens[1:]
        processed_types = processed_types[1:]
    if processed_tokens[-1] == '<EOL>':
        processed_tokens = processed_tokens[:-1]
        processed_types = processed_types[:-1]

    return processed_tokens, processed_types