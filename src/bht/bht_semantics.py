from transformers import BertTokenizer, BertModel
from transformers import RobertaTokenizer, RobertaModel
from sklearn.metrics.pairwise import cosine_similarity
import tensorflow as tf
import tensorflow_hub as hub
import torch
import spacy
import numpy as np

SPACY_LOADED = False
USE_LOADED = False

NLP = None
STOP_WORDS_SET = None
USE_MODEL = None

def load_spacy():
    global NLP, STOP_WORDS_SET, SPACY_LOADED

    # Load spaCy model
    print("Preparing spacy model...", flush=True)
    NLP = spacy.load("en_core_web_sm")
    STOP_WORDS_SET = spacy.lang.en.stop_words.STOP_WORDS # Get the list of English stopwords
    print("Done.", flush=True)
    SPACY_LOADED = True

def load_use():
    global USE_MODEL, USE_LOADED

    # Load the Universal Sentence Encoder model
    print("Preparing Universal Sentence Encoder model...", flush=True)
    USE_MODEL = hub.load("src/tensorflow_cache/universal-sentence-encoder_4/")
    print("Done.", flush=True)
    USE_LOADED = True

load_spacy()
load_use()


# TODO: Make this class make sense
class BHTSemantics:
    def __init__(self):
        pass

    def get_stop_words(self):
        if not SPACY_LOADED:
            load_spacy()

        return STOP_WORDS_SET

    def get_nlp(self):
        if not SPACY_LOADED:
            load_spacy()

        return NLP

    def load_universal_sentence_encoder(self):
        self.usb_loaded = True

    def calculate_similarity_bert(self, short_text, long_text):
        # Load pretrained BERT model and tokenizer
        model = BertModel.from_pretrained("bert-base-uncased")
        tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

        # Tokenize and encode the texts
        long_text_tokens = tokenizer(long_text, return_tensors="pt", padding=True, truncation=True)
        short_text_tokens = tokenizer(short_text, return_tensors="pt", padding=True, truncation=True)

        # Compute cosine similarity
        with torch.no_grad():
            # Get embeddings for the long text
            long_text_embeddings = model(**long_text_tokens)["last_hidden_state"].mean(dim=1)

            # Get embeddings for the short text
            short_text_embeddings = model(**short_text_tokens)["last_hidden_state"].mean(dim=1)

            # Calculate cosine similarity
            similarity_score = torch.cosine_similarity(long_text_embeddings, short_text_embeddings)

        return similarity_score.item()  # Convert the similarity score to a Python float

    def calculate_similarity_roberta(self, short_text, long_text):
        # Load pretrained RoBERTa model and tokenizer
        model = RobertaModel.from_pretrained("roberta-base")
        tokenizer = RobertaTokenizer.from_pretrained("roberta-base")

        # Tokenize and encode the texts
        long_text_tokens = tokenizer(long_text, return_tensors="pt", padding=True, truncation=True)
        short_text_tokens = tokenizer(short_text, return_tensors="pt", padding=True, truncation=True)

        # Compute cosine similarity
        with torch.no_grad():
            # Get embeddings for the long text
            long_text_embeddings = model(**long_text_tokens)["last_hidden_state"].mean(dim=1)

            # Get embeddings for the short text
            short_text_embeddings = model(**short_text_tokens)["last_hidden_state"].mean(dim=1)

            # Calculate cosine similarity
            similarity_score = torch.cosine_similarity(long_text_embeddings, short_text_embeddings)

        return similarity_score.item()  # Convert the similarity score to a Python float


    def calculate_similarity_sklearn(self, short_text, long_text):
        if not SPACY_LOADED:
            load_spacy()
        
        return cosine_similarity(NLP(long_text).vector.reshape(1, -1), NLP(short_text).vector.reshape(1, -1))[0][0]


    def calculate_similarity_tensorflow(self, text1, text2):
        if not USE_LOADED:
            load_use()

        # Encode the texts into fixed-dimensional vectors
        embedding1 = USE_MODEL([text1])
        embedding2 = USE_MODEL([text2])

        # Compute the cosine similarity between the encoded vectors
        similarity_score = cosine_similarity(np.array(embedding1), np.array(embedding2))

        return similarity_score[0][0]


if __name__ == '__main__':
    # Process original content and summary
    doc_original = """
1. "[Christ is] Head over all things to the Church, which same is His BODY, the fulness of Him who filleth all things." 
2. "The meaning being, that the church, being the Body of Christ, is dwelt in and filled by God: it is His πλήρωμα in an especial manner His fulness abides in it, and is exemplified by it." 
3. "The Church is the special receptacle and abiding place, the πλήρωμα κατ ʼ ἐξοχήν, of Him who fills all things."

1. "HIM He gave as Head over all things to the Church." 
2. "Had it been anyone save HIM, her Head, it would not have been the boon it is to the Church." 
3. "For the Head and body are not severed by anything intervening, else the body would cease to be the body, and the Head cease to be the Head."

1. "The universe is under his control and direction for the welfare of his people."
2. "All the elements - the physical works of God - the winds and waves - the seas and rivers - all are under him, and all are to be made tributary to the welfare of the church."
3. "Earthly kings and rulers; kingdoms and nations are under his control."

1. "Put all things in subjection." Compare Colossians 1:15-18; Psalms 8:5-8.
2. "Gave Him. Him is emphatic: and Him He gave." Not merely set Him over the Church, but gave Him as a gift. See 2 Corinthians 9:15.
3. "The Church [τη εκκλησια]. See on Matthew 16:18."

1. "He was made the head of the Church, on the condition that he should have the administration of all things."
2. "The metaphor of a head denotes the highest authority."
3. "The Church is His body, and, consequently, those who refuse to submit to Him are unworthy of its communion; for on Him alone the unity of the Church depends."

1. "The unlimited Sovereignty of the exalted Christ is now set forth: ‘all things’ sums up what has been detailed in Ephesians 1:21."
2. "The passage plainly says that Christ is given to the Church, and the next verse as plainly indicates that He is Head of the Church."
3. "The preservation of the Church throughout eighteen centuries is the accumulating proof that Christ is Head over all things to that Church."

1. "He put all things in subjection." 
2. "Gave him to be head." 
3. "Gave to the church Christ as Head."

1. "And hath put all things under his feet...." - These words are taken out of Psalms 8:6.
2. "Christ is an head to this church;... in what sense he is so, Psalms 8:6."
3. "And this headship of Christ is the gift of God;... and a giving him in all things the pre-eminence; and it is a free grace gift to the church, and a very special, valuable, and excellent one, and of infinite benefit and advantage to it."

1. "An head both of guidance and government, and likewise of life and influence, to the whole and every member of it."
2. "All these stand in the nearest union with him, and have as continual and effectual a communication of activity, growth, and strength from him..."
3. "...as the natural body from its head."
    """
                    
    doc_summary1 = """
Christ is the Head of the Church, possessing unlimited authority over all things. Just as the body is connected to its head, the Church is intimately linked to Christ, receiving guidance, government, life, and influence from Him. This special gift of headship from God has immense value and benefits the Church greatly, ensuring unity and the continuous flow of activity, growth, and strength to every member. This truth is beautifully illustrated in Psalms 8:6, where God puts all things under Christ's feet, reinforcing His supreme reign and the Church's reliance on Him.
    """

    doc_summary2 = """
Marriage is a divine union that God has joined together, and it should not be treated lightly. When two individuals come together in marriage, they become one both spiritually and emotionally. This unity is meant to be cherished and respected, as it is not easily dissolved. God's intention for marriage is to create an unbreakable bond, a oneness that should be honored and upheld throughout a lifetime.
    """

    bht_semantics = BHTSemantics()

    print("sklearn", bht_semantics.calculate_similarity_sklearn(doc_summary1, doc_original), bht_semantics.calculate_similarity_sklearn(doc_summary2, doc_original))
    print("bert", bht_semantics.calculate_similarity_bert(doc_summary1, doc_original), bht_semantics.calculate_similarity_bert(doc_summary2, doc_original))
    print("roberta", bht_semantics.calculate_similarity_roberta(doc_summary1, doc_original), bht_semantics.calculate_similarity_roberta(doc_summary2, doc_original))
    print("tensorflow", bht_semantics.calculate_similarity_tensorflow(doc_summary1, doc_original), bht_semantics.calculate_similarity_tensorflow(doc_summary2, doc_original))