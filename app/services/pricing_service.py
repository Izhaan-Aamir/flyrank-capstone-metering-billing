# Prices are integer micro-units per 1 million tokens.
INPUT_PRICE = 1_000_000
CACHED_INPUT_PRICE = 250_000
OUTPUT_PRICE = 2_000_000
REASONING_PRICE = 2_000_000


def calculate_cost(
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
    reasoning_tokens: int,
) -> int:
    regular_input_tokens = input_tokens - cached_input_tokens

    input_cost = (
        regular_input_tokens * INPUT_PRICE
        + cached_input_tokens * CACHED_INPUT_PRICE
    )

    output_cost = output_tokens * OUTPUT_PRICE
    reasoning_cost = reasoning_tokens * REASONING_PRICE

    return input_cost + output_cost + reasoning_cost