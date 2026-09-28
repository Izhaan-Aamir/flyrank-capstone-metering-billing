from app.services.pricing_service import calculate_cost


def test_calculate_cost():
    cost = calculate_cost(
        input_tokens=1000,
        cached_input_tokens=200,
        output_tokens=500,
        reasoning_tokens=100,
    )

    expected = (
        800 * 1_000_000
        + 200 * 250_000
        + 500 * 2_000_000
        + 100 * 2_000_000
    )

    assert cost == expected


def test_cached_tokens_are_not_double_charged():
    cost = calculate_cost(
        input_tokens=1000,
        cached_input_tokens=1000,
        output_tokens=0,
        reasoning_tokens=0,
    )

    assert cost == 1000 * 250_000

def test_reasoning_tokens_are_charged_as_output():
    cost = calculate_cost(
        input_tokens=0,
        cached_input_tokens=0,
        output_tokens=0,
        reasoning_tokens=100,
    )

    assert cost == 100 * 2_000_000

def test_zero_cached_input_uses_regular_input_price():
    cost = calculate_cost(
        input_tokens=100,
        cached_input_tokens=0,
        output_tokens=0,
        reasoning_tokens=0,
    )

    assert cost == 100 * 1_000_000