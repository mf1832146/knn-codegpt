import javalang.tokenizer
import tokenizers
import javalang
from transformers import GPT2Tokenizer

tokenizer = GPT2Tokenizer.from_pretrained("microsoft/CodeGPT-small-java-adaptedGPT2")

s = 'package org . apache . ws . security . dom . validate ; import java . io . IOException ; import javax . security . auth . callback . Callback ; import javax . security . auth . callback . UnsupportedCallbackException ; import org . apache . ws . security . dom . WSConstants ; import org . apache . ws . security . dom . WSSConfig ; import org . apache . ws . security . common . ext . WSPasswordCallback ; import org . apache . ws . security . common . ext . WSSecurityException ; import org . apache . ws . security . dom . handler . RequestData ; import org . apache . ws . security . dom . message . token . UsernameToken ; import org . apache . xml . security . exceptions . Base64DecodingException ; import org . apache . xml . security . utils . Base64 ; public class UsernameTokenValidator implements Validator { private static org . apache . commons . logging . Log log = org . apache . commons . logging . LogFactory . getLog ( UsernameTokenValidator . class ) ; public Credential validate ( Credential credential , RequestData data ) throws WSSecurityException { if ( credential = = null | | credential . getUsernametoken ( ) = = null ) { throw new WSSecurityException ( WSSecurityException . ErrorCode . FAILURE , \"<STR_LIT>\" ) ; }'

d = []

for i, v in enumerate(s.split()):
    if i > 0:
        v = ' ' + v
    t = tokenizer.encode(v)
    d.extend(t)

e = tokenizer.encode(s)

for i in range(len(e)):
    assert e[i] == d[i], f"{i}, {e[i]},{d[i]}"