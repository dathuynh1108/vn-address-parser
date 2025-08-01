from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline

tokenizer = AutoTokenizer.from_pretrained("NlpHUST/ner-vietnamese-electra-base")
model = AutoModelForTokenClassification.from_pretrained("NlpHUST/ner-vietnamese-electra-base")
nlp = pipeline("ner", model=model, tokenizer=tokenizer)
def group_and_clean_entities(entities, text):
    """Group B- and I- tags and handle subword tokens (##)"""
    grouped = []
    current_entity = None
    
    for ent in entities:
        entity_type = ent['entity']
        start, end = ent['start'], ent['end']
        word = ent['word']
        
        if entity_type.startswith('B-'):
            # Start new entity
            if current_entity:
                grouped.append(current_entity)
            
            current_entity = {
                'word': word,
                'entity': entity_type[2:],  # Remove B- prefix
                'score': ent['score'],
                'start': start,
                'end': end
            }
            
        elif entity_type.startswith('I-') and current_entity:
            # Continue current entity
            if word.startswith('##'):
                # Remove ## prefix and concatenate
                current_entity['word'] += word[2:]
            else:
                # Add space if it's a separate word
                current_entity['word'] += ' ' + word
            current_entity['end'] = end
            current_entity['score'] = min(current_entity['score'], ent['score'])
    
    if current_entity:
        grouped.append(current_entity)

    return grouped

def ner(text):
    entities = nlp(text)
    return group_and_clean_entities(entities, text)
