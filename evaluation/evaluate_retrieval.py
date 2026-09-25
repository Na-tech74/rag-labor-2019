import json
import sys
from pathlib import  Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.retriever import search

QUESTIONS_PATH = Path(r"D:\rag-labor-2019\evaluation\questions.json")

#Hàm nhận kết quả retrieval rồi tính các chỉ số đánh giá.
def caculate_metrics(results , relevant_articles, k):
    retrieved_articles =[
        result["article"]
        for result in results[:k]
    ]
    relevant =set(relevant_articles)
    
    #Hit@K trong Top-K có ít nhất một Điều đúng không?
    hit = any(
        article in relevant
        for article in retrieved_articles
    )
    
    #Recall@K đếm xem bao nhiêu Điều đúng đã được tìm thấy.
    found_relevant = sum(
        1
        for article in relevant
        if article in retrieved_articles
    )

    recall = found_relevant / len(relevant)
    
     # Precision@K trong các kết quả mà hệ thống lấy ra, có bao nhiêu kết quả đúng?
    relevant_retrieved = sum(
        1
        for article in retrieved_articles
        if article in relevant
    )

    precision = relevant_retrieved / k

     # MRR (Mean Reciprocal Rank) kết quả đúng đứng ở vị trí bao nhiêu?
    reciprocal_rank = 0

    for rank, article in enumerate(retrieved_articles,start=1):
        if article in relevant:
            reciprocal_rank = 1 / rank
            break
        
    return {
        "hit": int(hit),
        "recall": recall,
        "precision": precision,
        "mrr": reciprocal_rank
    }
    
def main():
    question =json.loads(
        QUESTIONS_PATH.read_text(encoding="utf-8")
    )
    
    total = len(question)
    
    total_hit = 0
    total_recall = 0
    total_precision = 0
    total_mrr = 0
    
    for index, item in enumerate(question, start=1):
        
        question =item["question"]
        relevant_articles =item["relevant_articles"]
        
        print("\n" + "=" * 70)
        print(f"CÂU {index}: {question}")
        print(
            f"Ground truth: "
            f"{', '.join(relevant_articles)}"
        )

        #Retrieval
        result = search(question , top_k=5)
        #Metrics
        metrics = caculate_metrics( result ,relevant_articles , k=5)
        
        total_hit += metrics["hit"]
        total_recall += metrics["recall"]
        total_precision += metrics["precision"]
        total_mrr += metrics["mrr"]
        
        print("\nRetrieved:")
        
        for rank , result in enumerate( result , start =1 ):
            print(
                f"{rank}. "
                f"{result['article']} | "
                f"{result['title']} | "
                f"Distance: "
                f"{result['distance']:.4f}"
            )
             
            print("\nMetrics:")
             
            print( f"Hit@5:        "f"{metrics['hit']}")
            print( f"Recall@5:     " f"{metrics['recall']:.4f}")
            print( f"Precision@5:  "f"{metrics['precision']:.4f}")
            print( f"MRR@5:        "f"{metrics['mrr']:.4f}" )

if __name__ == "__main__":
    main()