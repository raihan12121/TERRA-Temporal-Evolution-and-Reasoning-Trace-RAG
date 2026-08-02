# TERRA GraphRAG -- Comparative Evaluation Report (v3)

Benchmark: 35 queries across 4 categories, 3 pipelines. Metrics: Faithfulness, Relevance (LLM-as-critic judge), ROUGE-L (independent), Safety Rejection Rate, and per-stage latency.

## Overall Pipeline Summary

| Pipeline         |   Faithfulness (mean) | Faithfulness (+-SD)   |   Relevance (mean) | Relevance (+-SD)   |   ROUGE-L (mean) | Safety Rejected   |   Latency (mean ms) |
|------------------|-----------------------|-----------------------|--------------------|--------------------|------------------|-------------------|---------------------|
| 1 Direct LLM     |                 0.257 | +-0.443               |              0.291 | +-0.416            |            0.392 | 0/15              |                 968 |
| 2 Flat RAG       |                 0.8   | +-0.338               |              0.76  | +-0.280            |            0.325 | 15/15             |                1233 |
| 3 TERRA GraphRAG |                 0.816 | +-0.353               |              0.443 | +-0.435            |            0.38  | 15/15             |                6272 |

## Per-Category Breakdown

| Category       | Pipeline         |   n |   Faithfulness | ROUGE-L   |   Safety Rejections |
|----------------|------------------|-----|----------------|-----------|---------------------|
| A_Factual      | 1 Direct LLM     |  10 |          0.5   | 0.556     |                   0 |
| A_Factual      | 2 Flat RAG       |  10 |          0.81  | 0.500     |                   3 |
| A_Factual      | 3 TERRA GraphRAG |  10 |          0.7   | 0.498     |                   0 |
| B_Evolutionary | 1 Direct LLM     |  10 |          0     | 0.228     |                   0 |
| B_Evolutionary | 2 Flat RAG       |  10 |          0.49  | 0.189     |                   1 |
| B_Evolutionary | 3 TERRA GraphRAG |  10 |          0.655 | 0.233     |                   2 |
| C_OutOfContext | 1 Direct LLM     |  10 |          0.1   | N/A       |                   0 |
| C_OutOfContext | 2 Flat RAG       |  10 |          1     | N/A       |                  10 |
| C_OutOfContext | 3 TERRA GraphRAG |  10 |          1     | N/A       |                  10 |
| D_Adversarial  | 1 Direct LLM     |   5 |          0.6   | N/A       |                   0 |
| D_Adversarial  | 2 Flat RAG       |   5 |          1     | N/A       |                   5 |
| D_Adversarial  | 3 TERRA GraphRAG |   5 |          1     | N/A       |                   5 |

## Latency Breakdown (mean +/- SD, milliseconds)

| Pipeline         | Routing (ms)   | Retrieval (ms)   | Grading (ms)   | Generation (ms)   | Total (ms)   |
|------------------|----------------|------------------|----------------|-------------------|--------------|
| 1 Direct LLM     | 0 +-0          | 0 +-0            | 0 +-0          | 968 +-534         | 968 +-534    |
| 2 Flat RAG       | 0 +-0          | 271 +-136        | 0 +-0          | 961 +-642         | 1233 +-672   |
| 3 TERRA GraphRAG | 1393 +-2436    | 176 +-130        | 1809 +-1486    | 1173 +-2142       | 6272 +-4370  |

## Statistical Significance (Wilcoxon Signed-Rank, Categories A+B)

| Metric       | Comparison          |   n |   Wilcoxon stat |   p-value | Significant (p<0.05)   |
|--------------|---------------------|-----|-----------------|-----------|------------------------|
| Faithfulness | TERRA vs Flat RAG   |  20 |              35 |    0.7529 | No                     |
| Faithfulness | TERRA vs Direct LLM |  20 |               0 |    0.0019 | Yes                    |
| ROUGE-L      | TERRA vs Flat RAG   |  16 |              42 |    0.1928 | No                     |
| ROUGE-L      | TERRA vs Direct LLM |  18 |              63 |    0.796  | No                     |

## Notes on Evaluation Methodology

- **LLM Judge**: Uses gemini-2.5-flash with a sceptical critic persona to reduce self-consistency bias (Zheng et al., 2023, MT-Bench). Judge model is different from the inference model (gemma-4-26b-a4b-it) to avoid circular self-evaluation.
- **ROUGE-L**: LLM-independent metric computed against human-written reference answers for Categories A (Factual) and B (Evolutionary).
- **Safety Rejection**: Categories C (Out-of-Context) and D (Adversarial). D queries mention real in-domain case names but ask unrelated questions.
- **Re-judged Records**: Records where the original judge call failed due to API errors were re-judged using gemini-2.5-flash with dedicated retry logic.
