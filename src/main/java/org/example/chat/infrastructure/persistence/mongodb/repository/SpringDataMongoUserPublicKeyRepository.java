package org.example.chat.infrastructure.persistence.mongodb.repository;

import org.example.chat.infrastructure.persistence.mongodb.document.UserPublicKeyDocument;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface SpringDataMongoUserPublicKeyRepository extends MongoRepository<UserPublicKeyDocument, String> {
    Optional<UserPublicKeyDocument> findByUserId(String userId);
}
