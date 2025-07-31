import json
import re

def tokenize(text):
    # Tách từ và giữ lại dấu câu
    text = re.sub(r'([.,!?()])', r' \1 ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip().split()

def tag_phrase(tokens, phrase, tag_type):
    if not phrase:
        return False

    phrase_tokens = tokenize(phrase.lower())
    token_texts = [t[0].lower() for t in tokens]
    print("Phrase tokens", phrase_tokens)
    
    for i in range(len(tokens) - len(phrase_tokens) + 1):
        window = token_texts[i:i+len(phrase_tokens)]
        
        print("Window", window, token_texts)
        
        if window == phrase_tokens:
            tokens[i] = (tokens[i][0], f'B-{tag_type}')
            for j in range(1, len(phrase_tokens)):
                tokens[i + j] = (tokens[i + j][0], f'I-{tag_type}')
            return True
    
    return False

text = "The quick brown fox jumps over the lazy dog."
phrase = "the quick"
tokens = tokenize(text)
tokens = [(token, 'O') for token in tokens]
tags = tag_phrase(tokens, phrase, 'COLOR')
print(tokens)