"""Fit compact evidence against the serving tokenizer, before generating prose."""
MAX_TOKENS = 7263


class PromptBudgetError(ValueError):
    pass


def fit(mind, build, chars, thinking=False):
    """Only the evidence allowance shrinks; critical records never get cut.

    Stub minds generate no real text and need no tokenizer. HTTPMind always
    provides the server's tokenizer, so a real compact prompt fails closed.
    """
    count = getattr(mind, 'prompt_tokens', None)
    value = build(chars)
    if not callable(count):
        return value
    size = count(value, thinking=thinking)
    while size > MAX_TOKENS:
        if chars <= 300:
            raise PromptBudgetError(f'Compact prompt has {size} tokens; cannot fit within {MAX_TOKENS} while preserving required evidence')
        next_chars = max(300, chars - max(128, min(chars // 2, (size - MAX_TOKENS) * 3)))
        chars = next_chars
        value = build(chars)
        size = count(value, thinking=thinking)
    return value
