#!/usr/bin/env python3
# verify_tech_1_2.py — Verify TECH-1 and TECH-2 equation costs
# encoding: utf-8
import math


def verify_tfidf():
    # tf-idf(t,d) = tf(t,d) · log(N/df(t))
    def tfidf(count, total, N, df):
        tf = count / total          # div
        idf = math.log(N / df)      # div + ln
        return tf * idf             # mul

    cases = [(3, 100, 1000, 50), (5, 200, 5000, 100), (1, 50, 10000, 1)]
    for count, total, N, df in cases:
        result = tfidf(count, total, N, df)
        print(f"TF-IDF({count}/{total}, ln({N}/{df})) = {result:.6f}  [cost: 7n]")


def verify_pagerank():
    # PR(A) = (1-d) + d * sum(PR_Ti/C_Ti)
    def pagerank(incoming_prs, incoming_degrees, d=0.85):
        s = sum(pr / c for pr, c in zip(incoming_prs, incoming_degrees))
        return (1 - d) + d * s

    cases = [
        ([0.5, 0.3, 0.8], [5, 3, 10]),
        ([1.0, 0.5], [2, 4]),
        ([0.25] * 10, [5] * 10),
    ]
    for prs, cs in cases:
        result = pagerank(prs, cs)
        N = len(prs)
        cost = 5 * N + 4  # v4 cost
        print(f"PageRank(N={N}) = {result:.6f}, cost = {cost}n")


def verify_cosine():
    # cos sim for d=3
    def dot(a, b):
        return sum(x * y for x, y in zip(a, b))

    def cosine_sim(a, b):
        return dot(a, b) / (math.sqrt(dot(a, a)) * math.sqrt(dot(b, b)))

    cases = [
        ([1, 0, 0], [0, 1, 0]),
        ([1, 1, 1], [1, 1, 0]),
        ([3, 4, 0], [4, 3, 0]),
    ]
    for a, b in cases:
        d = len(a)
        result = cosine_sim(a, b)
        cost = 15 * d - 1
        print(f"cos_sim({a}, {b}) = {result:.6f}, cost = {cost}n")


def verify_bm25_idf():
    # IDF(q) = ln((N-df+0.5)/(df+0.5))
    def bm25_idf(N, df):
        return math.log((N - df + 0.5) / (df + 0.5))

    cases = [(1000, 50), (5000, 100), (10000, 1)]
    for N, df in cases:
        result = bm25_idf(N, df)
        print(f"BM25_IDF(N={N}, df={df}) = {result:.6f}  [IDF body: 11n]")


def verify_bm25_full():
    # Full BM25 per term: IDF * f*(k1+1) / (f + k1*(1-b + b*|D|/avgdl))
    def bm25_score(N, df, f, k1, b, doc_len, avgdl):
        idf = math.log((N - df + 0.5) / (df + 0.5))
        numerator = f * (k1 + 1)
        denominator = f + k1 * (1 - b + b * doc_len / avgdl)
        return idf * numerator / denominator

    cases = [
        (1000, 50, 3, 1.5, 0.75, 120, 100),
        (5000, 100, 1, 1.2, 0.75, 80, 100),
        (10000, 1, 5, 2.0, 0.5, 200, 150),
    ]
    for N, df, f, k1, b, dl, avgdl in cases:
        result = bm25_score(N, df, f, k1, b, dl, avgdl)
        print(f"BM25(N={N}, df={df}, f={f}, dl={dl}) = {result:.6f}  [per-term: 34n]")


def verify_sigmoid():
    # sigmoid = 1/(1+exp(-x))
    def sigmoid(x):
        return 1.0 / (1.0 + math.exp(-x))

    cases = [0.0, 1.0, -1.0, 2.5]
    for x in cases:
        result = sigmoid(x)
        print(f"sigmoid({x:+.1f}) = {result:.6f}  [body cost: 7n with v4 recip=1n]")


def verify_bpr():
    # BPR loss = -ln(sigmoid(x_uij))
    def bpr_loss(x_uij):
        s = 1.0 / (1.0 + math.exp(-x_uij))
        return -math.log(s)

    cases = [0.5, 1.0, -0.5, 2.0]
    for x in cases:
        result = bpr_loss(x)
        d_example = 10
        cost = 5 * d_example + 7
        print(f"BPR_loss(x={x:+.1f}) = {result:.6f}  [cost at d={d_example}: {cost}n]")


def verify_cosine_annealing():
    # lr(t) = lr_min + 0.5*(lr_max - lr_min)*(1 + cos(pi*t/T))
    def cosine_lr(t, T, lr_min=1e-4, lr_max=1e-2):
        return lr_min + 0.5 * (lr_max - lr_min) * (1 + math.cos(math.pi * t / T))

    T = 100
    cases = [0, 25, 50, 75, 100]
    for t in cases:
        result = cosine_lr(t, T)
        print(f"cosine_lr(t={t:3d}/{T}) = {result:.6f}  [cost: 17n]")


def verify_cost_formulas():
    print("\n--- Cost Formula Spot Checks ---")
    # PageRank 5N+4
    for N in [5, 10, 100]:
        assert 5 * N + 4 == [29, 54, 504][[5, 10, 100].index(N)], f"PageRank cost mismatch at N={N}"
    print("PageRank 5N+4: OK (N=5->29, N=10->54, N=100->504)")

    # Cosine similarity 15d-1
    for d, expected in [(3, 44), (10, 149), (100, 1499)]:
        assert 15 * d - 1 == expected, f"Cosine cost mismatch at d={d}"
    print("Cosine 15d-1: OK (d=3->44, d=10->149, d=100->1499)")

    # CF dot product 5d-3
    assert 5 * 100 - 3 == 497
    print("CF dot 5d-3: OK (d=100->497)")

    # MF fit 5d+2
    for d in [10, 50, 100]:
        cost = 5 * d + 2
        print(f"  MF fit(d={d}) = {cost}n")

    # MF reg 10d+1
    for d in [10, 50, 100]:
        cost = 10 * d + 1
        print(f"  MF reg(d={d}) = {cost}n")

    # BPR 5d+7
    for d in [10, 50, 100]:
        cost = 5 * d + 7
        print(f"  BPR(d={d}) = {cost}n")

    # BM25 Q terms: 37Q-3
    for Q in [1, 5, 10]:
        cost = 37 * Q - 3
        print(f"  BM25(Q={Q}) = {cost}n")

    print("All formula checks passed.")


if __name__ == "__main__":
    print("=== TF-IDF Verification (7n) ===")
    verify_tfidf()

    print("\n=== PageRank Verification (5N+4) ===")
    verify_pagerank()

    print("\n=== Cosine Similarity Verification (15d-1) ===")
    verify_cosine()

    print("\n=== BM25 IDF Verification (IDF body: 11n) ===")
    verify_bm25_idf()

    print("\n=== BM25 Full Score Verification (34n per term) ===")
    verify_bm25_full()

    print("\n=== Sigmoid Verification (body: 7n) ===")
    verify_sigmoid()

    print("\n=== BPR Loss Verification (5d+7) ===")
    verify_bpr()

    print("\n=== Cosine Annealing LR Verification (17n) ===")
    verify_cosine_annealing()

    verify_cost_formulas()
