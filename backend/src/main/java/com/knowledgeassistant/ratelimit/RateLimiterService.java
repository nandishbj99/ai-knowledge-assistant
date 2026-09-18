package com.knowledgeassistant.ratelimit;

import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.ClassPathResource;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Collections;
import java.util.List;

@Service
public class RateLimiterService {

    private static final Logger log = LoggerFactory.getLogger(RateLimiterService.class);

    private final StringRedisTemplate redisTemplate;
    private DefaultRedisScript<List> redisScript;

    public RateLimiterService(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    @PostConstruct
    public void init() {
        redisScript = new DefaultRedisScript<>();
        redisScript.setLocation(new ClassPathResource("scripts/rate_limiter.lua"));
        redisScript.setResultType(List.class);
    }

    public RateLimitResult checkLimit(String key, int capacity, double refillRate, int requestedTokens, int ttlSeconds) {
        try {
            long now = Instant.now().getEpochSecond();
            List<Object> results = redisTemplate.execute(
                    redisScript,
                    Collections.singletonList(key),
                    String.valueOf(capacity),
                    String.valueOf(refillRate),
                    String.valueOf(now),
                    String.valueOf(requestedTokens),
                    String.valueOf(ttlSeconds)
            );

            if (results != null && results.size() >= 3) {
                long allowedVal = ((Number) results.get(0)).longValue();
                int remaining = ((Number) results.get(1)).intValue();
                int retryAfter = ((Number) results.get(2)).intValue();
                return new RateLimitResult(allowedVal == 1L, remaining, retryAfter);
            }
        } catch (Exception e) {
            log.error("Rate limiter evaluation failed for key {}. Falling back to permit.", key, e);
            return new RateLimitResult(true, capacity, 0);
        }

        return new RateLimitResult(true, capacity, 0);
    }
}
