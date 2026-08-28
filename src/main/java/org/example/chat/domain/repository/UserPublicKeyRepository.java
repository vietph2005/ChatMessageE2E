package org.example.chat.domain.repository;

import org.example.chat.domain.model.UserPublicKeyBundle;

import java.util.Optional;

public interface UserPublicKeyRepository {
    UserPublicKeyBundle save(UserPublicKeyBundle bundle);
    Optional<UserPublicKeyBundle> findByUserId(String userId);
}
