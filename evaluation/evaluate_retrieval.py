import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config import QUESTIONS_PATH
from src.retriever import search

TOP_K = 5


def calculate_metrics(results, relevant_articles, k=TOP_K):
    """Tính Hit@K, Recall@K, Precision@K và MRR cho một câu hỏi."""
    retrieved_articles = [r["article"] for r in results[:k]]
    relevant = set(relevant_articles)

    # Hit@K: trong Top-K có ít nhất một Điều đúng không?
    hit = any(article in relevant for article in retrieved_articles)

    # Recall@K: bao nhiêu Điều đúng đã được tìm thấy?
    found = sum(1 for article in relevant if article in retrieved_articles)
    recall = found / len(relevant) if relevant else 0.0

    # Precision@K: trong K kết quả trả về, có bao nhiêu kết quả đúng?
    correct = sum(1 for article in retrieved_articles if article in relevant)
    precision = correct / k if k else 0.0

    # MRR: kết quả đúng đứng ở vị trí bao nhiêu?
    mrr = 0.0
    for rank, article in enumerate(retrieved_articles, start=1):
        if article in relevant:
            mrr = 1 / rank
            break

    return {"hit": int(hit), "recall": recall, "precision": precision, "mrr": mrr}


def main():
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    totals = {"hit": 0.0, "recall": 0.0, "precision": 0.0, "mrr": 0.0}

    for index, item in enumerate(questions, start=1):
        question = item["question"]
        relevant_articles = item["relevant_articles"]

        print("\n" + "=" * 70)
        print(f"CÂU {index}: {question}")
        print(f"Ground truth: {', '.join(relevant_articles)}")

        results = search(question, top_k=TOP_K)
        metrics = calculate_metrics(results, relevant_articles, k=TOP_K)

        print("\nRetrieved:")
        if not results:
            print("  (không có kết quả nào vượt ngưỡng khoảng cách)")
        for rank, result in enumerate(results, start=1):
            print(
                f"  {rank}. {result['article']} | {result['title']} | "
                f"Distance: {result['distance']:.4f}"
            )

        print(f"\nHit@{TOP_K}:        {metrics['hit']}")
        print(f"Recall@{TOP_K}:     {metrics['recall']:.4f}")
        print(f"Precision@{TOP_K}:  {metrics['precision']:.4f}")
        print(f"MRR@{TOP_K}:        {metrics['mrr']:.4f}")

        for key in totals:
            totals[key] += metrics[key]

    total = len(questions)
    print("\n" + "=" * 70)
    print("TỔNG KẾT")
    print("=" * 70)
    print(f"Số câu đánh giá:   {total}")
    print(f"Hit rate:           {totals['hit'] / total:.4f}")
    print(f"Mean Recall@{TOP_K}:    {totals['recall'] / total:.4f}")
    print(f"Mean Precision@{TOP_K}: {totals['precision'] / total:.4f}")
    print(f"MRR:                {totals['mrr'] / total:.4f}")


if __name__ == "__main__":
    main()
