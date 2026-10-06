# Perplexity on Hegel's text (6 October 2026)

`python3 tools/hegel_test.py --export-ppl mind/results/ppl` (seed 1831), then `llama-perplexity -c 512 -ngl 99` on the PC (llama.cpp b11429, WSL), the Qwen3.8-27B GGUF with and without the first adapter (rank 16, October 2026). Lower is better.

| file | what it is | plain Qwen | with the adapter | change |
|---|---|---|---|---|
| heldout.txt | the 20 real passages of the Hegel test, left out of the training | 9.548 ± 0.632 | 9.012 ± 0.587 | −5.6% |
| seen.txt | 20 passages of the same books that were in the training | 14.535 ± 1.044 | 12.795 ± 0.884 | −12.0% |

The adapter predicts his text a little better, the text it saw about twice as much as the text it did not. The two files' absolute values are not comparable: seen.txt keeps some scan errors that the hand-fixed held-out passages lack.
