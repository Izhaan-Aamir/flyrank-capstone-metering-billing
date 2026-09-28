CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    api_call_limit BIGINT NOT NULL CHECK (api_call_limit >= 0),
    ai_token_limit BIGINT NOT NULL CHECK (ai_token_limit >= 0),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL UNIQUE REFERENCES tenants(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES plans(id),
    status VARCHAR(30) NOT NULL CHECK (
        status IN ('active', 'trialing', 'past_due', 'canceled')
    ),
    stripe_customer_id VARCHAR(255) UNIQUE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    usage_type VARCHAR(30) NOT NULL CHECK (
        usage_type IN ('api_calls', 'ai_tokens')
    ),
    quantity BIGINT NOT NULL CHECK (quantity > 0),
    idempotency_key VARCHAR(255) NOT NULL,

    input_tokens BIGINT NOT NULL DEFAULT 0
        CHECK (input_tokens >= 0),

    cached_input_tokens BIGINT NOT NULL DEFAULT 0
        CHECK (
            cached_input_tokens >= 0
            AND cached_input_tokens <= input_tokens
        ),

    output_tokens BIGINT NOT NULL DEFAULT 0
        CHECK (output_tokens >= 0),

    reasoning_tokens BIGINT NOT NULL DEFAULT 0
        CHECK (reasoning_tokens >= 0),

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_usage_events_tenant_idempotency
        UNIQUE (tenant_id, idempotency_key)
);

CREATE TABLE stripe_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_event_id VARCHAR(255) NOT NULL UNIQUE,
    event_type VARCHAR(100) NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_plan_id
    ON subscriptions(plan_id);

CREATE INDEX idx_usage_events_tenant_occurred_at
    ON usage_events(tenant_id, occurred_at);

CREATE INDEX idx_usage_events_tenant_usage_type_occurred_at
    ON usage_events(tenant_id, usage_type, occurred_at);

CREATE INDEX idx_stripe_events_event_type
    ON stripe_events(event_type);