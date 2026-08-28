package org.example.chat.infrastructure.persistence.mongodb.repository;

import lombok.RequiredArgsConstructor;
import org.example.chat.domain.model.UserProfile;
import org.example.chat.domain.repository.UserRepository;
import org.example.chat.infrastructure.persistence.mongodb.document.UserDocument;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.Optional;

@Component
@RequiredArgsConstructor
public class UserRepositoryImpl implements UserRepository {

    private final SpringDataMongoUserRepository mongoRepository;

    @Override
    public UserProfile save(UserProfile user) {
        UserDocument doc = toDocument(user);
        UserDocument saved = mongoRepository.save(doc);
        return toDomain(saved);
    }

    @Override
    public Optional<UserProfile> findById(String id) {
        return mongoRepository.findById(id).map(this::toDomain);
    }

    @Override
    public Optional<UserProfile> findByGoogleSubjectId(String googleSubjectId) {
        return mongoRepository.findByGoogleSubjectId(googleSubjectId).map(this::toDomain);
    }

    @Override
    public Optional<UserProfile> findByEmail(String email) {
        return mongoRepository.findByEmail(email.toLowerCase().trim()).map(this::toDomain);
    }

    @Override
    public void updateOnlineStatus(String userId, boolean isOnline) {
        mongoRepository.findById(userId).ifPresent(doc -> {
            doc.setOnline(isOnline);
            doc.setLastSeenAt(Instant.now());
            mongoRepository.save(doc);
        });
    }

    private UserDocument toDocument(UserProfile user) {
        return UserDocument.builder()
                .id(user.getId())
                .googleSubjectId(user.getGoogleSubjectId())
                .email(user.getEmail() != null ? user.getEmail().toLowerCase().trim() : null)
                .displayName(user.getDisplayName())
                .avatarUrl(user.getAvatarUrl())
                .createdAt(user.getCreatedAt())
                .lastSeenAt(user.getLastSeenAt())
                .isOnline(user.isOnline())
                .build();
    }

    private UserProfile toDomain(UserDocument doc) {
        return UserProfile.builder()
                .id(doc.getId())
                .googleSubjectId(doc.getGoogleSubjectId())
                .email(doc.getEmail())
                .displayName(doc.getDisplayName())
                .avatarUrl(doc.getAvatarUrl())
                .createdAt(doc.getCreatedAt())
                .lastSeenAt(doc.getLastSeenAt())
                .isOnline(doc.isOnline())
                .build();
    }
}
