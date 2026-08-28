package org.example.chat.domain.repository;

import org.example.chat.domain.model.UserProfile;

import java.util.Optional;

public interface UserRepository {
    UserProfile save(UserProfile user);
    Optional<UserProfile> findById(String id);
    Optional<UserProfile> findByGoogleSubjectId(String googleSubjectId);
    Optional<UserProfile> findByEmail(String email);
    void updateOnlineStatus(String userId, boolean isOnline);
}
