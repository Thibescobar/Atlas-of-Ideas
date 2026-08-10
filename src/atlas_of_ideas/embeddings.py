from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class LocalEmbedder:
    '''
    Deliberately simple baseline.

    Start with TF-IDF so the whole project runs locally and transparently.
    Replace it later with sentence-transformers or an embedding API.
    '''

    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))

    def fit_transform(self, texts: list[str]):
        return self.vectorizer.fit_transform(texts)

    @staticmethod
    def similarities(matrix):
        return cosine_similarity(matrix)
