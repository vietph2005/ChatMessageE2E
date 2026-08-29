package org.example.chat.contract;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.example.chat.domain.model.UserProfile;
import org.example.chat.domain.model.UserPublicKeyBundle;
import org.example.chat.domain.repository.UserPublicKeyRepository;
import org.example.chat.domain.repository.UserRepository;
import org.example.chat.infrastructure.security.JwtTokenProvider;
import org.example.chat.presentation.dto.AuthDto;
import org.example.chat.presentation.dto.PublicKeyBundleDto;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.time.Instant;
import java.util.Optional;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class AuthApiContractTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private JwtTokenProvider jwtTokenProvider;

    @MockBean
    private UserRepository userRepository;

    @MockBean
    private UserPublicKeyRepository userPublicKeyRepository;

    @Test
    @DisplayName("Contract: POST /api/v1/auth/google should authenticate and return tokens and set ACCESS_TOKEN cookie")
    void testGoogleAuthEndpoint() throws Exception {
        UserProfile user = UserProfile.builder()
                .id("user_test_123")
                .googleSubjectId("google-sub-alice@gmail.com")
                .email("alice@gmail.com")
                .displayName("Alice")
                .avatarUrl("https://avatar.com/alice.png")
                .createdAt(Instant.now())
                .lastSeenAt(Instant.now())
                .isOnline(true)
                .build();

        when(userRepository.findByGoogleSubjectId(any())).thenReturn(Optional.of(user));
        when(userRepository.save(any())).thenReturn(user);

        AuthDto.GoogleAuthRequest request = new AuthDto.GoogleAuthRequest("mock-google-token-alice@gmail.com");

        mockMvc.perform(post("/api/v1/auth/google")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accessToken").isNotEmpty())
                .andExpect(jsonPath("$.user.email").value("alice@gmail.com"))
                .andExpect(jsonPath("$.user.displayName").value("alice"))
                .andExpect(result -> {
                    String setCookie = result.getResponse().getHeader("Set-Cookie");
                    org.junit.jupiter.api.Assertions.assertNotNull(setCookie);
                    org.junit.jupiter.api.Assertions.assertTrue(setCookie.contains("ACCESS_TOKEN="));
                    org.junit.jupiter.api.Assertions.assertTrue(setCookie.contains("HttpOnly"));
                });
    }

    @Test
    @DisplayName("Contract: GET /api/v1/auth/me should authenticate using ACCESS_TOKEN cookie")
    void testAuthMeWithCookie() throws Exception {
        UserProfile user = UserProfile.builder()
                .id("user_test_123")
                .googleSubjectId("google-sub-alice@gmail.com")
                .email("alice@gmail.com")
                .displayName("Alice")
                .avatarUrl("https://avatar.com/alice.png")
                .createdAt(Instant.now())
                .lastSeenAt(Instant.now())
                .isOnline(true)
                .build();

        when(userRepository.findById("user_test_123")).thenReturn(Optional.of(user));

        String token = jwtTokenProvider.generateToken("user_test_123", "alice@gmail.com", "Alice");

        jakarta.servlet.http.Cookie authCookie = new jakarta.servlet.http.Cookie("ACCESS_TOKEN", token);

        mockMvc.perform(get("/api/v1/auth/me")
                        .cookie(authCookie))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value("user_test_123"))
                .andExpect(jsonPath("$.email").value("alice@gmail.com"));
    }

    @Test
    @DisplayName("Contract: POST /api/v1/auth/logout should clear ACCESS_TOKEN cookie")
    void testAuthLogout() throws Exception {
        mockMvc.perform(post("/api/v1/auth/logout"))
                .andExpect(status().isOk())
                .andExpect(result -> {
                    String setCookie = result.getResponse().getHeader("Set-Cookie");
                    org.junit.jupiter.api.Assertions.assertNotNull(setCookie);
                    org.junit.jupiter.api.Assertions.assertTrue(setCookie.contains("ACCESS_TOKEN="));
                    org.junit.jupiter.api.Assertions.assertTrue(setCookie.contains("Max-Age=0"));
                });
    }

    @Test
    @DisplayName("Contract: GET /api/v1/users/search by exact Gmail should return user")
    void testExactGmailSearchEndpoint() throws Exception {
        UserProfile user = UserProfile.builder()
                .id("user_test_456")
                .email("bob@gmail.com")
                .displayName("Bob")
                .avatarUrl("https://avatar.com/bob.png")
                .isOnline(true)
                .build();

        when(userRepository.findByEmail("bob@gmail.com")).thenReturn(Optional.of(user));

        String token = jwtTokenProvider.generateToken("user_test_123", "alice@gmail.com", "Alice");

        mockMvc.perform(get("/api/v1/users/search")
                        .header("Authorization", "Bearer " + token)
                        .param("email", "bob@gmail.com"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.email").value("bob@gmail.com"))
                .andExpect(jsonPath("$.displayName").value("Bob"));
    }

    @Test
    @DisplayName("Contract: POST and GET /api/v1/users/keys")
    void testUserKeysEndpoint() throws Exception {
        UserPublicKeyBundle bundle = UserPublicKeyBundle.builder()
                .userId("user_test_123")
                .identityPublicKey("MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...")
                .signedPreKey("MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...")
                .keyVersion(1)
                .build();

        when(userPublicKeyRepository.findByUserId("user_test_123")).thenReturn(Optional.of(bundle));
        when(userPublicKeyRepository.save(any())).thenReturn(bundle);

        String token = jwtTokenProvider.generateToken("user_test_123", "alice@gmail.com", "Alice");

        PublicKeyBundleDto dto = PublicKeyBundleDto.builder()
                .identityPublicKey("MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...")
                .signedPreKey("MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...")
                .build();

        mockMvc.perform(post("/api/v1/users/keys")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(dto)))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/v1/users/keys")
                        .header("Authorization", "Bearer " + token)
                        .param("userId", "user_test_123"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.identityPublicKey").isNotEmpty());
    }
}
