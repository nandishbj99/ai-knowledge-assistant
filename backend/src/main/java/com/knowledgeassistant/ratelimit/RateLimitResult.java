package com.knowledgeassistant.ratelimit;

public record RateLimitResult(boolean allowed, int remainingTokens, int retryAfterSeconds) {}
