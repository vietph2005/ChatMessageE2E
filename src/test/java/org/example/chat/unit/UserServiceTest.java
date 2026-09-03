package org.example.chat.unit;

import org.example.chat.application.service.UserService;
import org.example.chat.domain.exception.DomainException;
import org.example.chat.domain.model.UserProfile;
import org.example.chat.domain.model.UserPublicKeyBundle;
import org.example.chat.domain.repository.UserPublicKeyRepository;
import org.example.chat.domain.repository.UserRepository;
import org.example.chat.infrastructure.security.GoogleTokenVerifier;
import org.example.chat.infrastructure.security.JwtTokenProvider;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.HashSet;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private UserPublicKeyRepository userPublicKeyRepository;

    @Mock
    private GoogleTokenVerifier googleTokenVerifier;

    @Mock
    private JwtTokenProvider jwtTokenProvider;

    @InjectMocks
    private UserService userService;

    @Nested
    @DisplayName("searchByExactGmail tests")
    class SearchByExactGmailTests {

        @Test
        @DisplayName("Should find user and normalize email with trim and lowercase")
        void shouldFindUserAndNormalizeEmail() {
            // 1. Arrange
            UserProfile mockUser = UserProfile.builder()
                    .id("user_bob")
                    .email("bob@gmail.com")
                    .displayName("Bob")
                    .build();

            when(userRepository.findByEmail("bob@gmail.com")).thenReturn(Optional.of(mockUser));

            // 2. Act
            UserProfile result = userService.searchByExactGmail("  Bob@GMAIL.com  ");

            // 3. Assert
            assertNotNull(result);
            assertEquals("user_bob", result.getId());
            assertEquals("bob@gmail.com", result.getEmail());
            verify(userRepository, times(1)).findByEmail("bob@gmail.com");
        }

        @Test
        @DisplayName("Should throw DomainException when user email is not found")
        void shouldThrowExceptionWhenEmailNotFound() {
            // 1. Arrange
            when(userRepository.findByEmail("notfound@gmail.com")).thenReturn(Optional.empty());

            // 2 & 3. Act & Assert
            DomainException exception = assertThrows(DomainException.class, () -> {
                userService.searchByExactGmail("notfound@gmail.com");
            });

            assertEquals("USER_NOT_FOUND", exception.getErrorCode());
        }
    }

    @Nested
    @DisplayName("getUserById tests")
    class GetUserByIdTests {

        @Test
        @DisplayName("Should return user when ID exists")
        void shouldReturnUserWhenIdExists() {
            UserProfile mockUser = UserProfile.builder()
                    .id("user_123")
                    .email("alice@gmail.com")
                    .displayName("Alice")
                    .build();

            when(userRepository.findById("user_123")).thenReturn(Optional.of(mockUser));

            UserProfile result = userService.getUserById("user_123");

            assertNotNull(result);
            assertEquals("user_123", result.getId());
        }

        @Test
        @DisplayName("Should throw DomainException when ID does not exist")
        void shouldThrowExceptionWhenIdNotFound() {
            when(userRepository.findById("invalid_id")).thenReturn(Optional.empty());

            DomainException exception = assertThrows(DomainException.class, () -> {
                userService.getUserById("invalid_id");
            });

            assertEquals("USER_NOT_FOUND", exception.getErrorCode());
        }
    }

    @Nested
    @DisplayName("Public Key Bundle tests")
    class PublicKeyBundleTests {

        @Test
        @DisplayName("Should register public key bundle with updated timestamp and user ID")
        void shouldRegisterPublicKeyBundle() {
            UserPublicKeyBundle bundle = UserPublicKeyBundle.builder()
                    .identityPublicKey("SPKI_PUB_KEY")
                    .signedPreKey("SPKI_SIGNED_PRE_KEY")
                    .build();

            userService.registerPublicKeyBundle("user_123", bundle);

            assertEquals("user_123", bundle.getUserId());
            assertNotNull(bundle.getUpdatedAt());
            verify(userPublicKeyRepository, times(1)).save(bundle);
        }

        @Test
        @DisplayName("Should return public key bundle when exists")
        void shouldReturnPublicKeyBundleWhenExists() {
            UserPublicKeyBundle bundle = UserPublicKeyBundle.builder()
                    .userId("user_123")
                    .identityPublicKey("SPKI_PUB_KEY")
                    .build();

            when(userPublicKeyRepository.findByUserId("user_123")).thenReturn(Optional.of(bundle));

            UserPublicKeyBundle result = userService.getPublicKeyBundle("user_123");

            assertNotNull(result);
            assertEquals("user_123", result.getUserId());
        }

        @Test
        @DisplayName("Should throw DomainException when public key bundle not found")
        void shouldThrowExceptionWhenKeysNotFound() {
            when(userPublicKeyRepository.findByUserId("user_unknown")).thenReturn(Optional.empty());

            DomainException exception = assertThrows(DomainException.class, () -> {
                userService.getPublicKeyBundle("user_unknown");
            });

            assertEquals("KEYS_NOT_FOUND", exception.getErrorCode());
        }
    }

    @Nested
    @DisplayName("blockUser and unblockUser tests")
    class BlockAndUnblockTests {

        @Test
        @DisplayName("Should add target user ID to blocked list when blocking")
        void shouldBlockUserSuccessfully() {
            UserProfile user = UserProfile.builder()
                    .id("user_alice")
                    .email("alice@gmail.com")
                    .blockedUserIds(new HashSet<>())
                    .build();

            when(userRepository.findById("user_alice")).thenReturn(Optional.of(user));

            userService.blockUser("user_alice", "user_spammer");

            assertTrue(user.getBlockedUserIds().contains("user_spammer"));
            verify(userRepository, times(1)).save(user);
        }

        @Test
        @DisplayName("Should remove target user ID from blocked list when unblocking")
        void shouldUnblockUserSuccessfully() {
            HashSet<String> blocked = new HashSet<>();
            blocked.add("user_spammer");

            UserProfile user = UserProfile.builder()
                    .id("user_alice")
                    .email("alice@gmail.com")
                    .blockedUserIds(blocked)
                    .build();

            when(userRepository.findById("user_alice")).thenReturn(Optional.of(user));

            userService.unblockUser("user_alice", "user_spammer");

            assertFalse(user.getBlockedUserIds().contains("user_spammer"));
            verify(userRepository, times(1)).save(user);
        }
    }

    @Nested
    @DisplayName("authenticateWithGoogle tests")
    class GoogleAuthTests {

        @Test
        @DisplayName("Should update existing user and generate JWT token")
        void shouldUpdateExistingUserOnGoogleAuth() {
            GoogleTokenVerifier.GoogleUserPayload payload = GoogleTokenVerifier.GoogleUserPayload.builder()
                    .subjectId("google_sub_123")
                    .email("alice@gmail.com")
                    .displayName("Alice New Name")
                    .avatarUrl("https://avatar.com/new.png")
                    .emailVerified(true)
                    .build();

            UserProfile existingUser = UserProfile.builder()
                    .id("user_alice")
                    .googleSubjectId("google_sub_123")
                    .email("alice@gmail.com")
                    .displayName("Alice Old Name")
                    .build();

            when(googleTokenVerifier.verify("valid_google_token")).thenReturn(payload);
            when(userRepository.findByGoogleSubjectId("google_sub_123")).thenReturn(Optional.of(existingUser));
            when(userRepository.save(any(UserProfile.class))).thenAnswer(i -> i.getArgument(0));
            when(jwtTokenProvider.generateToken("user_alice", "alice@gmail.com", "Alice New Name"))
                    .thenReturn("mock_jwt_access_token");

            UserService.AuthResult authResult = userService.authenticateWithGoogle("valid_google_token");

            assertNotNull(authResult);
            assertEquals("mock_jwt_access_token", authResult.accessToken());
            assertEquals("Alice New Name", authResult.user().getDisplayName());
            assertTrue(authResult.user().isOnline());
        }

        @Test
        @DisplayName("Should create new user profile when signing in for the first time")
        void shouldCreateNewUserOnFirstGoogleAuth() {
            GoogleTokenVerifier.GoogleUserPayload payload = GoogleTokenVerifier.GoogleUserPayload.builder()
                    .subjectId("google_sub_456")
                    .email("bob@gmail.com")
                    .displayName("Bob")
                    .avatarUrl("https://avatar.com/bob.png")
                    .emailVerified(true)
                    .build();

            when(googleTokenVerifier.verify("first_time_token")).thenReturn(payload);
            when(userRepository.findByGoogleSubjectId("google_sub_456")).thenReturn(Optional.empty());
            when(userRepository.save(any(UserProfile.class))).thenAnswer(i -> {
                UserProfile u = i.getArgument(0);
                u.setId("new_user_bob_id");
                return u;
            });
            when(jwtTokenProvider.generateToken("new_user_bob_id", "bob@gmail.com", "Bob"))
                    .thenReturn("bob_jwt_token");

            UserService.AuthResult authResult = userService.authenticateWithGoogle("first_time_token");

            assertNotNull(authResult);
            assertEquals("bob_jwt_token", authResult.accessToken());
            assertEquals("bob@gmail.com", authResult.user().getEmail());
            assertEquals("new_user_bob_id", authResult.user().getId());
        }
    }
}
