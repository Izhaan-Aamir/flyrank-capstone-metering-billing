from pydantic import BaseModel, Field, model_validator


class GenerateRequest(BaseModel):
    input_tokens: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    reasoning_tokens: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_token_breakdown(self):
        if self.cached_input_tokens > self.input_tokens:
            raise ValueError(
                "cached_input_tokens cannot exceed input_tokens."
            )

        total_tokens = (
            self.input_tokens
            + self.output_tokens
            + self.reasoning_tokens
        )

        if total_tokens <= 0:
            raise ValueError(
                "At least one token quantity must be greater than zero."
            )

        return self


class UsageResponse(BaseModel):
    usage_event_id: str
    tenant_key: str
    usage_type: str
    quantity: int
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    reasoning_tokens: int