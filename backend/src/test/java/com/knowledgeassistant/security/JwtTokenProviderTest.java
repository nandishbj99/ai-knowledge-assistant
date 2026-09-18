package com.knowledgeassistant.security;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

import java.util.Collections;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class JwtTokenProviderTest {

    private JwtTokenProvider tokenProvider;
    private final String testSecret = "9a78bf234c90de45f871234098bc1234567890abcdef1234567890abcdef";
    private final long accessExpiration = 900000; // 15 min
    private final long refreshExpiration = 604800000; // 7 days

    @BeforeEach
    void setUp() {
        tokenProvider = new JwtTokenProvider(testSecret, accessExpiration, refreshExpiration);
    }

    @Test
    void testGenerateAndValidateAccessToken() {
        UUID userId = UUID.randomUUID();
        UUID tenantId = UUID.randomUUID();
        UserPrincipal principal = new UserPrincipal(
                userId,
                tenantId,
                "alice@example.com",
                "secret",
                Collections.singletonList(new SimpleGrantedAuthority("ROLE_USER"))
        );

        String token = tokenProvider.generateAccessToken(principal);
        assertNotNull(token);
        assertTrue(tokenProvider.validateToken(token));

        assertEquals(userId, tokenProvider.getUserIdFromToken(token));
        assertEquals(tenantId, tokenProvider.getTenantIdFromToken(token));
        assertNotNull(tokenProvider.getJtiFromToken(token));
        assertTrue(tokenProvider.getRemainingTtlSeconds(token) > 0);
    }

    @Test
    void testGenerateRefreshToken() {
        UUID userId = UUID.randomUUID();
        UUID tenantId = UUID.randomUUID();
        UserPrincipal principal = new UserPrincipal(
                userId,
                tenantId,
                "bob@example.com",
                "secret",
                Collections.singletonList(new SimpleGrantedAuthority("ROLE_USER"))
        );

        String refreshToken = tokenProvider.generateRefreshToken(principal);
        assertNotNull(refreshToken);
        assertTrue(tokenProvider.validateToken(refreshToken));
        assertEquals(userId, tokenProvider.getUserIdFromToken(refreshToken));
        assertEquals(tenantId, tokenProvider.getTenantIdFromToken(refreshToken));
    }

    @Test
    void testInvalidTokenRejection() {
        assertFalse(tokenProvider.validateToken("invalid.jwt.token"));
    }
}
