"""Incremental token counter backed by tiktoken with an Anthropic SDK fallback for accurate per-model counts."""

import warnings

_ENCODING = None


def _get_encoding():
    """Lazy initialize tiktoken cl100k_base encoding.
    
    Returns the encoding object on first call, cached thereafter.
    """
    global _ENCODING
    if _ENCODING is None:
        import tiktoken
        _ENCODING = tiktoken.get_encoding("cl100k_base")
    return _ENCODING


def _encode_message(message: dict, enc) -> int:
    """Encode a message and return token count with overhead.
    
    Args:
        message: Message dict with optional "content" key
        enc: tiktoken encoding object
        
    Returns:
        Number of tokens (content tokens + 4 for role overhead)
    """
    content = message.get("content")
    if content is None or content == "":
        return 4
    
    encoded = enc.encode(content)
    return len(encoded) + 4


def estimate_tokens_fast(messages: list[dict]) -> int:
    """Fast heuristic token estimate without tiktoken.
    
    Args:
        messages: List of message dicts
        
    Returns:
        Estimated token count based on character count
    """
    total_chars = sum(len(m.get("content") or "") for m in messages)
    return total_chars // 4


def count_tokens_delta(
    messages: list[dict], prev_token_total: int, prev_msg_count: int
) -> int:
    """Count tokens for new messages and add to previous total.
    
    Args:
        messages: Full list of messages
        prev_token_total: Token count from previous call
        prev_msg_count: Number of messages already counted
        
    Returns:
        Updated total token count including new messages + 3 (reply primer)
        
    Raises:
        No exceptions - falls back to estimate on error
    """
    try:
        enc = _get_encoding()
        
        # Tokenize only new messages
        delta_tokens = sum(
            _encode_message(m, enc) for m in messages[prev_msg_count:]
        )
        
        return prev_token_total + delta_tokens + 3
    except Exception as e:
        warnings.warn(
            f"tiktoken failed: {e}, falling back to estimate",
            RuntimeWarning,
            stacklevel=2,
        )
        fallback_delta = estimate_tokens_fast(messages[prev_msg_count:])
        return prev_token_total + fallback_delta + 3
