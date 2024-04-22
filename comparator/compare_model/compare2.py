from sentence_transformers import SentenceTransformer

# sentences = [
#     "I like rainy days because they make me feel relaxed.",
#     "I don't like rainy days because they don't make me feel relaxed."
# ]

# model = SentenceTransformer('dmlls/all-mpnet-base-v2-negation')
# embeddings = model.encode(sentences)
# from sklearn.metrics.pairwise import cosine_similarity

# similarity_score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
# similarity = (similarity_score + 1) / 2 

# print("Similarity:", similarity)

def checkSimilarity(text1, text2):
    model = SentenceTransformer('dmlls/all-mpnet-base-v2-negation')
    embeddings = model.encode([text1, text2])
    from sklearn.metrics.pairwise import cosine_similarity

    similarity_score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    similarity = (similarity_score + 1) / 2 

    return similarity