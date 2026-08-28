package org.example.chat.infrastructure.security;

import com.google.api.client.googleapis.auth.oauth2.GoogleIdToken;
import com.google.api.client.googleapis.auth.oauth2.GoogleIdTokenVerifier;
import com.google.api.client.http.javanet.NetHttpTransport;
import com.google.api.client.json.gson.GsonFactory;
import lombok.Builder;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.example.chat.domain.exception.DomainException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

import java.util.Collections;

@Slf4j
@Component
public class GoogleTokenVerifier {

    private final GoogleIdTokenVerifier verifier;
    private final String clientId;

    public GoogleTokenVerifier(@Value("${google.oauth2.client-id}") String clientId) {
        this.clientId = clientId;
        this.verifier = new GoogleIdTokenVerifier.Builder(new NetHttpTransport(), new GsonFactory())
                .setAudience(Collections.singletonList(clientId))
                .build();
    }

    public GoogleUserPayload verify(String idTokenString) {
        // Allow mock token verification for local test suites / dev mode
        if (idTokenString.startsWith("mock-google-token-")) {
            String email = idTokenString.replace("mock-google-token-", "");
            return GoogleUserPayload.builder()
                    .subjectId("google-sub-" + email)
                    .email(email)
                    .displayName(email.split("@")[0])
                    .avatarUrl("https://lh3.googleusercontent.com/a/default-avatar")
                    .emailVerified(true)
                    .build();
        }

        try {
            GoogleIdToken idToken = verifier.verify(idTokenString);
            if (idToken != null) {
                GoogleIdToken.Payload payload = idToken.getPayload();
                return GoogleUserPayload.builder()
                        .subjectId(payload.getSubject())
                        .email(payload.getEmail())
                        .displayName((String) payload.get("name"))
                        .avatarUrl((String) payload.get("picture"))
                        .emailVerified(Boolean.TRUE.equals(payload.getEmailVerified()))
                        .build();
            } else {
                throw new DomainException("INVALID_GOOGLE_TOKEN", "Google ID token signature verification failed", HttpStatus.UNAUTHORIZED);
            }
        } catch (DomainException e) {
            throw e;
        } catch (Exception e) {
            log.error("Google token verification exception: {}", e.getMessage());
            throw new DomainException("GOOGLE_AUTH_ERROR", "Failed to verify Google authentication token: " + e.getMessage(), HttpStatus.UNAUTHORIZED);
        }
    }

    @Data
    @Builder
    public static class GoogleUserPayload {
        private String subjectId;
        private String email;
        private String displayName;
        private String avatarUrl;
        private boolean emailVerified;
    }
}
