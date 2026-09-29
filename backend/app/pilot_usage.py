def usage_tokens(attempt):
    usage = attempt.get("usage") or {}
    input_tokens = usage.get("input_tokens")
    if input_tokens is None:
        input_tokens = usage.get("prompt_tokens")
    output_tokens = usage.get("output_tokens")
    if output_tokens is None:
        output_tokens = usage.get("completion_tokens")
    try:
        input_tokens = max(0, int(input_tokens or 0))
    except (TypeError, ValueError):
        input_tokens = 0
    try:
        output_tokens = max(0, int(output_tokens or 0))
    except (TypeError, ValueError):
        output_tokens = 0
    return input_tokens, output_tokens
