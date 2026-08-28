package org.example.chat.unit;

import org.example.chat.infrastructure.security.JwtTokenProvider;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class JwtTokenProviderTest {

    private JwtTokenProvider jwtTokenProvider;
    private static final String TEST_SECRET = "super_secure_jwt_testing_secret_key_at_least_256_bits_long_abcdef123456";

    @BeforeEach
    void setUp() {
        jwtTokenProvider = new JwtTokenProvider(TEST_SECRET, 3600000);
    }

    @Test
    @DisplayName("Should generate and validate JWT token successfully")
    void shouldGenerateAndValidateToken() {
        String userId = "user_12345";
        String email = "test@gmail.com";
        String displayName = "Test User";

        String token = jwtTokenProvider.generateToken(userId, email, displayName);

        assertNotNull(token);
        assertTrue(jwtTokenProvider.validateToken(token));
        assertEquals(userId, jwtTokenProvider.getUserIdFromToken(token));
        assertEquals(email, jwtTokenProvider.getEmailFromToken(token));
    }

    @Test
    @DisplayName("Should reject invalid or tampered JWT token")
    void shouldRejectInvalidToken() {
        String invalidToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalidPayload.invalidSignature";
        assertFalse(jwtTokenProvider.validateToken(invalidToken));
    }
}
