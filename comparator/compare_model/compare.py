from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F


def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[
        0
    ] 
    input_mask_expanded = (
        attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    )
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
        input_mask_expanded.sum(1), min=1e-9
    )

def cosine_similarity(u, v):
    return F.cosine_similarity(u, v, dim=1)


def compare(text1, text2):

    sentences = [text1, text2]

    tokenizer = AutoTokenizer.from_pretrained("dmlls/all-mpnet-base-v2-negation")
    model = AutoModel.from_pretrained("dmlls/all-mpnet-base-v2-negation")

    encoded_input = tokenizer(
        sentences, padding=True, truncation=True, return_tensors="pt"
    )

    with torch.no_grad():
        model_output = model(**encoded_input)

    sentence_embeddings = mean_pooling(model_output, encoded_input["attention_mask"])

    sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

    similarity_score = cosine_similarity(
        sentence_embeddings[0].unsqueeze(0), sentence_embeddings[1].unsqueeze(0)
    )
    return similarity_score.item()