import tiktoken


def add_text_till_limit(it, max_tokens, joiner, fuzz=.75):
    text = ""
    tokens = 0
    for t in it:
        num_tokens = len(tiktoken.get_encoding("gpt2").encode(t))
        if tokens + num_tokens >= max_tokens:
            text += joiner + t[:int(len(t) * (max_tokens - tokens) / num_tokens * fuzz)]
            break
        tokens += num_tokens
        text += joiner + t
    return text, tokens