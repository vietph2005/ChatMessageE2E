package org.example.chat.application.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.example.chat.domain.exception.DomainException;
import org.example.chat.domain.model.UserProfile;
import org.example.chat.domain.model.UserPublicKeyBundle;
import org.example.chat.domain.repository.UserPublicKeyRepository;
import org.example.chat.domain.repository.UserRepository;
import org.example.chat.infrastructure.security.GoogleTokenVerifier;
import org.example.chat.infrastructure.security.JwtTokenProvider;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

import java.time.Instant;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    private final UserPublicKeyRepository userPublicKeyRepository;
    private final GoogleTokenVerifier googleTokenVerifier;
    private final JwtTokenProvider jwtTokenProvider;

    public AuthResult authenticateWithGoogle(String idToken) {
        GoogleTokenVerifier.GoogleUserPayload payload = googleTokenVerifier.verify(idToken);

        UserProfile user = userRepository.findByGoogleSubjectId(payload.getSubjectId())
                .map(existing -> {
                    existing.setDisplayName(payload.getDisplayName());
                    existing.setAvatarUrl(payload.getAvatarUrl());
                    existing.setLastSeenAt(Instant.now());
                    existing.setOnline(true);
                    return userRepository.save(existing);
                })
                .orElseGet(() -> {
                    UserProfile newUser = UserProfile.builder()
                            .googleSubjectId(payload.getSubjectId())
                            .email(payload.getEmail().toLowerCase().trim())
                            .displayName(payload.getDisplayName() != null ? payload.getDisplayName() : payload.getEmail().split("@")[0])
                            .avatarUrl(payload.getAvatarUrl())
                            .createdAt(Instant.now())
                            .lastSeenAt(Instant.now())
                            .isOnline(true)
                            .build();
                    log.info("[UserService] Creating new user: {}", newUser.getEmail());
                    return userRepository.save(newUser);
                });

        String accessToken = jwtTokenProvider.generateToken(user.getId(), user.getEmail(), user.getDisplayName());

        return new AuthResult(accessToken, 86400000L, user);
    }

    public UserProfile searchByExactGmail(String email) {
        String normalizedEmail = email.toLowerCase().trim();
        return userRepository.findByEmail(normalizedEmail)
                .orElseThrow(() -> new DomainException("USER_NOT_FOUND", "No user found with exact Gmail: " + normalizedEmail, HttpStatus.NOT_FOUND));
    }

    public UserProfile getUserById(String userId) {
        return userRepository.findById(userId)
                .orElseThrow(() -> new DomainException("USER_NOT_FOUND", "User not found: " + userId, HttpStatus.NOT_FOUND));
    }

    public void registerPublicKeyBundle(String userId, UserPublicKeyBundle bundle) {
        bundle.setUserId(userId);
        bundle.setUpdatedAt(Instant.now());
        userPublicKeyRepository.save(bundle);
        log.info("[UserService] Registered public keys for user: {}", userId);
    }

    public UserPublicKeyBundle getPublicKeyBundle(String userId) {
        return userPublicKeyRepository.findByUserId(userId)
                .orElseThrow(() -> new DomainException("KEYS_NOT_FOUND", "Public keys not found for user: " + userId, HttpStatus.NOT_FOUND));
    }

    public record AuthResult(String accessToken, long expiresIn, UserProfile user) {}
}
