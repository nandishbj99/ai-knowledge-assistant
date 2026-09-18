package com.knowledgeassistant.service;

import com.knowledgeassistant.domain.entity.User;
import com.knowledgeassistant.domain.repository.UserRepository;
import com.knowledgeassistant.security.JwtTokenProvider;
import com.knowledgeassistant.security.UserPrincipal;
import com.knowledgeassistant.web.dto.*;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.util.UUID;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider tokenProvider;
    private final StringRedisTemplate redisTemplate;

    public AuthService(
            UserRepository userRepository,
            PasswordEncoder passwordEncoder,
            JwtTokenProvider tokenProvider,
            StringRedisTemplate redisTemplate) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.tokenProvider = tokenProvider;
        this.redisTemplate = redisTemplate;
    }

    @Transactional
    public AuthResponse register(RegisterRequest request) {
        if (userRepository.existsByEmail(request.email().toLowerCase().trim())) {
            throw new IllegalArgumentException("Email already registered: " + request.email());
        }

        UUID tenantId = request.tenantId() != null ? request.tenantId() : UUID.randomUUID();
        String hashedPassword = passwordEncoder.encode(request.password());

        User user = new User(
                tenantId,
                request.email().toLowerCase().trim(),
                hashedPassword,
                request.fullName().trim(),
                "ROLE_USER"
        );

        user = userRepository.save(user);
        UserPrincipal principal = UserPrincipal.create(user);

        String accessToken = tokenProvider.generateAccessToken(principal);
        String refreshToken = tokenProvider.generateRefreshToken(principal);

        return AuthResponse.of(
                accessToken,
                refreshToken,
                900, // 15 minutes
                new UserSummary(user.getId(), user.getTenantId(), user.getEmail(), user.getFullName(), user.getRole())
        );
    }

    @Transactional(readOnly = true)
    public AuthResponse login(LoginRequest request) {
        User user = userRepository.findByEmail(request.email().toLowerCase().trim())
                .orElseThrow(() -> new BadCredentialsException("Invalid email or password"));

        if (!passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            throw new BadCredentialsException("Invalid email or password");
        }

        UserPrincipal principal = UserPrincipal.create(user);
        String accessToken = tokenProvider.generateAccessToken(principal);
        String refreshToken = tokenProvider.generateRefreshToken(principal);

        return AuthResponse.of(
                accessToken,
                refreshToken,
                900,
                new UserSummary(user.getId(), user.getTenantId(), user.getEmail(), user.getFullName(), user.getRole())
        );
    }

    @Transactional(readOnly = true)
    public AuthResponse refresh(RefreshTokenRequest request) {
        String token = request.refreshToken();
        if (!tokenProvider.validateToken(token)) {
            throw new BadCredentialsException("Invalid or expired refresh token");
        }

        UUID userId = tokenProvider.getUserIdFromToken(token);
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new BadCredentialsException("User not found"));

        UserPrincipal principal = UserPrincipal.create(user);
        String newAccessToken = tokenProvider.generateAccessToken(principal);
        String newRefreshToken = tokenProvider.generateRefreshToken(principal);

        return AuthResponse.of(
                newAccessToken,
                newRefreshToken,
                900,
                new UserSummary(user.getId(), user.getTenantId(), user.getEmail(), user.getFullName(), user.getRole())
        );
    }

    public void logout(String authHeader) {
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            if (tokenProvider.validateToken(token)) {
                String jti = tokenProvider.getJtiFromToken(token);
                long ttl = tokenProvider.getRemainingTtlSeconds(token);
                if (ttl > 0 && jti != null) {
                    redisTemplate.opsForValue().set("bl:token:" + jti, "revoked", Duration.ofSeconds(ttl));
                }
            }
        }
    }
}
