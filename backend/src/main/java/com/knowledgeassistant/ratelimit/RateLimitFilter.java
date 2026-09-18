package com.knowledgeassistant.ratelimit;

import com.knowledgeassistant.security.UserPrincipal;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.annotation.Order;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
@Order(10) // Executes after JwtAuthenticationFilter
public class RateLimitFilter extends OncePerRequestFilter {

    private final RateLimiterService rateLimiterService;

    public RateLimitFilter(RateLimiterService rateLimiterService) {
        this.rateLimiterService = rateLimiterService;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        String path = request.getRequestURI();

        // Skip internal/error paths
        if (path.startsWith("/error") || path.startsWith("/actuator")) {
            filterChain.doFilter(request, response);
            return;
        }

        String key;
        int capacity;
        double refillRate;
        int ttl;

        // Determine rate limit profile based on route and security context
        if (path.startsWith("/api/v1/auth")) {
            String clientIp = getClientIp(request);
            key = "rl:auth:" + clientIp;
            capacity = 10;
            refillRate = 0.16; // 10/min
            ttl = 120;
        } else {
            Authentication auth = SecurityContextHolder.getContext().getAuthentication();
            if (auth != null && auth.getPrincipal() instanceof UserPrincipal principal) {
                String tenantUser = principal.getTenantId() + ":" + principal.getId();
                if (path.contains("/documents/upload")) {
                    key = "rl:upload:" + tenantUser;
                    capacity = 5;
                    refillRate = 0.008; // 5/hour
                    ttl = 14400;
                } else if (path.contains("/query")) {
                    key = "rl:chat:" + tenantUser;
                    capacity = 30;
                    refillRate = 0.5; // 30/min
                    ttl = 180;
                } else {
                    key = "rl:read:" + tenantUser;
                    capacity = 120;
                    refillRate = 2.0; // 120/min
                    ttl = 120;
                }
            } else {
                filterChain.doFilter(request, response);
                return;
            }
        }

        RateLimitResult result = rateLimiterService.checkLimit(key, capacity, refillRate, 1, ttl);

        if (!result.allowed()) {
            response.setStatus(429); // Too Many Requests
            response.setHeader("Retry-After", String.valueOf(result.retryAfterSeconds()));
            response.setHeader("X-RateLimit-Limit", String.valueOf(capacity));
            response.setHeader("X-RateLimit-Remaining", "0");
            response.setContentType("application/json");
            response.getWriter().write(String.format("{\"error\": \"Too Many Requests\", \"retryAfterSeconds\": %d}", result.retryAfterSeconds()));
            return;
        }

        response.setHeader("X-RateLimit-Limit", String.valueOf(capacity));
        response.setHeader("X-RateLimit-Remaining", String.valueOf(result.remainingTokens()));
        response.setHeader("X-RateLimit-Reset", String.valueOf(result.retryAfterSeconds()));

        filterChain.doFilter(request, response);
    }

    private String getClientIp(HttpServletRequest request) {
        String xfHeader = request.getHeader("X-Forwarded-For");
        if (xfHeader == null || xfHeader.isEmpty()) {
            return request.getRemoteAddr();
        }
        return xfHeader.split(",")[0].trim();
    }
}
