"""Retrieval eval: recall@k, precision@k and MRR for several chunk sizes. Local only, no API cost.

Each question has a gold phrase from the source docs; a retrieved chunk counts as relevant
if it contains that phrase. Questions are paraphrased so they can't match on wording alone.

    .venv/bin/python rag_eval.py
"""
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter

import rag  # noqa: F401  (sets the same local embedding model)

EVAL = [
    ("How many free days do we get at West Coast ports before demurrage?", "4 calendar days from discharge"),
    ("What does demurrage cost in the first few days after free time?", "150 USD per container per day"),
    ("What is the daily demurrage rate after a container has been late a week?", "300 USD per day from day 5"),
    ("What is the difference between demurrage and detention?", "Detention is charged when the container is outside"),
    ("When do we warn customers that free time is running out?", "1 day from the end of its free time"),
    ("How long does a customer have to dispute a demurrage invoice?", "within 30 days of the invoice date"),
    ("What causes CBP to hold a container?", "Common causes"),
    ("When is the ISF filing due?", "24 hours before vessel loading"),
    ("How much delay does a customs exam add?", "3 to 10 days"),
    ("Who pays for a CBP exam?", "paid by the importer of record"),
    ("How fast must the broker reply to CBP?", "within 2 business days"),
    ("Does demurrage stop during a customs exam?", "does not pause demurrage"),
    ("How quickly must we tell a customer about a long delay?", "within 4 business hours"),
    ("What do we offer when the carrier rolls a booking?", "offer the next sailing"),
    ("What is the deadline to file a damage claim with the carrier?", "open a claim with the carrier within 3 days"),
    ("Can the system issue a customer credit without a person?", "An operator must approve any customer credit above 500 USD"),
]

K = 3


def score(chunk_size: int, overlap: int):
    docs = SimpleDirectoryReader("docs").load_data()
    nodes = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=overlap).get_nodes_from_documents(docs)
    retriever = VectorStoreIndex(nodes).as_retriever(similarity_top_k=K)
    recall = precision = rr = 0.0
    misses = []
    for question, gold in EVAL:
        hits = retriever.retrieve(question)
        relevant = [gold in h.get_content() for h in hits]
        recall += any(relevant)                     # one gold chunk per question, so recall@k = hit rate
        precision += sum(relevant) / K
        rr += next((1 / (i + 1) for i, r in enumerate(relevant) if r), 0)
        if not any(relevant):
            misses.append(question)
    n = len(EVAL)
    return len(nodes), recall / n, precision / n, rr / n, misses


if __name__ == "__main__":
    print(f"{len(EVAL)} questions, k={K}\n")
    print(f"{'chunk/overlap':>14} {'chunks':>7} {'recall@3':>9} {'precision@3':>12} {'MRR':>6}")
    for size, overlap in [(256, 32), (96, 16), (48, 8)]:
        n_chunks, r, p, mrr, misses = score(size, overlap)
        print(f"{f'{size}/{overlap}':>14} {n_chunks:>7} {r:>9.2f} {p:>12.2f} {mrr:>6.2f}")
        for q in misses:
            print(f"{'':>16}missed: {q}")
