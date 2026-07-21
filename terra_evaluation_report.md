# TERRA GraphRAG -- Comparative Evaluation Report (v3)

Benchmark: 35 queries across 4 categories, 3 pipelines. Metrics: Faithfulness, Relevance (LLM-as-critic judge), ROUGE-L (independent), Safety Rejection Rate, and per-stage latency.

## Overall Pipeline Summary

| Pipeline         |   Faithfulness (mean) | Faithfulness (+-SD)   |   Relevance (mean) | Relevance (+-SD)   |   ROUGE-L (mean) | Safety Rejected   |   Latency (mean ms) |
|------------------|-----------------------|-----------------------|--------------------|--------------------|------------------|-------------------|---------------------|
| 1 Direct LLM     |                 0.943 | +-0.236               |              1     | +-0.000            |            0.478 | 0/15              |               13310 |
| 2 Flat RAG       |                 0.971 | +-0.169               |              0.951 | +-0.203            |            0.301 | 14/15             |               12788 |
| 3 TERRA GraphRAG |                 0.772 | +-0.399               |              0.838 | +-0.363            |            0.259 | 15/15             |              376331 |

## Per-Category Breakdown

| Category       | Pipeline         |   n |   Faithfulness | ROUGE-L   |   Safety Rejections |
|----------------|------------------|-----|----------------|-----------|---------------------|
| A_Factual      | 1 Direct LLM     |  10 |          1     | 0.692     |                   0 |
| A_Factual      | 2 Flat RAG       |  10 |          1     | 0.357     |                   1 |
| A_Factual      | 3 TERRA GraphRAG |  10 |          1     | 0.275     |                   0 |
| B_Evolutionary | 1 Direct LLM     |  10 |          1     | 0.265     |                   0 |
| B_Evolutionary | 2 Flat RAG       |  10 |          0.9   | 0.229     |                   3 |
| B_Evolutionary | 3 TERRA GraphRAG |  10 |          0.325 | 0.237     |                   3 |
| C_OutOfContext | 1 Direct LLM     |  10 |          0.8   | N/A       |                   0 |
| C_OutOfContext | 2 Flat RAG       |  10 |          1     | N/A       |                  10 |
| C_OutOfContext | 3 TERRA GraphRAG |  10 |          0.889 | N/A       |                  10 |
| D_Adversarial  | 1 Direct LLM     |   5 |          1     | N/A       |                   0 |
| D_Adversarial  | 2 Flat RAG       |   5 |          1     | N/A       |                   4 |
| D_Adversarial  | 3 TERRA GraphRAG |   5 |          1     | N/A       |                   5 |

## Latency Breakdown (mean +/- SD, milliseconds)

| Pipeline         | Routing (ms)   | Retrieval (ms)   | Grading (ms)    | Generation (ms)   | Total (ms)      |
|------------------|----------------|------------------|-----------------|-------------------|-----------------|
| 1 Direct LLM     | 0 +-0          | 0 +-0            | 0 +-0           | 13310 +-7176      | 13310 +-7176    |
| 2 Flat RAG       | 0 +-0          | 217 +-87         | 0 +-0           | 12571 +-14476     | 12788 +-14482   |
| 3 TERRA GraphRAG | 14172 +-4616   | 161 +-114        | 171445 +-117647 | 53571 +-105092    | 376331 +-238039 |

## Statistical Significance (Wilcoxon Signed-Rank, Categories A+B)

| Metric       | Comparison          |   n |   Wilcoxon stat |   p-value | Significant (p<0.05)   |
|--------------|---------------------|-----|-----------------|-----------|------------------------|
| Faithfulness | TERRA vs Flat RAG   |  20 |               0 |    0.0235 | Yes                    |
| Faithfulness | TERRA vs Direct LLM |  20 |               0 |    0.0141 | Yes                    |
| ROUGE-L      | TERRA vs Flat RAG   |  16 |              58 |    0.9096 | No                     |
| ROUGE-L      | TERRA vs Direct LLM |  17 |              26 |    0.0298 | Yes                    |

## Notes on Evaluation Methodology

- **LLM Judge**: Uses gemini-2.5-flash with a sceptical critic persona to reduce self-consistency bias (Zheng et al., 2023, MT-Bench). Judge model is different from the inference model (gemma-4-26b-a4b-it) to avoid circular self-evaluation.
- **ROUGE-L**: LLM-independent metric computed against human-written reference answers for Categories A (Factual) and B (Evolutionary).
- **Safety Rejection**: Categories C (Out-of-Context) and D (Adversarial). D queries mention real in-domain case names but ask unrelated questions.
- **Re-judged Records**: Records where the original judge call failed due to API errors were re-judged using gemini-2.5-flash with dedicated retry logic.
