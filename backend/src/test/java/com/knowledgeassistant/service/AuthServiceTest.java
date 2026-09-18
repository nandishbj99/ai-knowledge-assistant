package com.knowledgeassistant.service;

import com.knowledgeassistant.domain.entity.User;
import com.knowledgeassistant.domain.repository.UserRepository;
import com.knowledgeassistant.security.JwtTokenProvider;
import com.knowledgeassistant.web.dto.AuthResponse;
import com.knowledgeassistant.web.dto.LoginRequest;
import com.knowledgeassistant.web.dto.RegisterRequest;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private JwtTokenProvider tokenProvider;

    @Mock
    private StringRedisTemplate redisTemplate;

    private AuthService authService;

    @BeforeEach
    void setUp() {
        authService = new AuthService(userRepository, passwordEncoder, tokenProvider, redisTemplate);
    }

    @Test
    void testRegisterSuccess() {
        RegisterRequest request = new RegisterRequest("test@example.com", "Password123!", "Test User", null);

        when(userRepository.existsByEmail("test@example.com")).thenReturn(false);
        when(passwordEncoder.encode("Password123!")).thenReturn("hashed_pass");
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> {
            User u = invocation.getArgument(0);
            u.setId(UUID.randomUUID());
            return u;
        });
        when(tokenProvider.generateAccessToken(any())).thenReturn("access_token");
        when(tokenProvider.generateRefreshToken(any())).thenReturn("refresh_token");

        AuthResponse response = authService.register(request);
        assertNotNull(response);
        assertEquals("access_token", response.accessToken());
        assertEquals("test@example.com", response.user().email());
    }

    @Test
    void testRegisterDuplicateEmailThrows() {
        RegisterRequest request = new RegisterRequest("existing@example.com", "Password123!", "Existing User", null);
        when(userRepository.existsByEmail("existing@example.com")).thenReturn(true);

        assertThrows(IllegalArgumentException.class, () -> authService.register(request));
    }

    @Test
    void testLoginInvalidPasswordThrows() {
        LoginRequest request = new LoginRequest("test@example.com", "WrongPassword");
        User user = new User(UUID.randomUUID(), "test@example.com", "hashed_pass", "Test User", "ROLE_USER");

        when(userRepository.findByEmail("test@example.com")).thenReturn(Optional.of(user));
        when(passwordEncoder.matches("WrongPassword", "hashed_pass")).thenReturn(false);

        assertThrows(BadCredentialsException.class, () -> authService.login(request));
    }
}
