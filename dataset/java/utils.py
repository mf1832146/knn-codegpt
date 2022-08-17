import re
import javalang
import json
from javalang.tokenizer import *


lits = json.load(open("../literals.json"))

token_types = {'BOS': 1,
               'Literals': 2,
               'Punctuation': 3,
               'Operator': 4,
               'Identifier': 5,
               'Keyword': 6
               }

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


def deal_with_java(code):
    code_tokens = []
    code_types = []
    tokens = list(javalang.tokenizer.tokenize(code))
    for i, tok in enumerate(tokens):
        if "String" in str(type(tok)) or "Character" in str(type(tok)):
            token = process_string(tok.value)
            code_type = 'Literals'
        elif "Integer" in str(type(tok)) or "FloatingPoint" in str(type(tok)):
            if tok.value in lits['num']:
                token = f"<NUM_LIT:{tok.value}>"
            else:
                token = "<NUM_LIT>"
            code_type = 'Literals'
        else:
            token = tok.value

            if isinstance(tok, Separator):
                code_type = 'Punctuation'

            elif isinstance(tok, Operator):
                code_type = 'Operator'
            elif isinstance(tok, Identifier):
                code_type = 'Identifier'

            else:
                code_type = 'Keyword'
        code_tokens.append(token)
        code_types.append(token_types[code_type])

    return code_tokens, code_types