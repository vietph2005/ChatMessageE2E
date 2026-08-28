package org.example.chat.infrastructure.persistence.mongodb.repository;

import org.example.chat.infrastructure.persistence.mongodb.document.UserDocument;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface SpringDataMongoUserRepository extends MongoRepository<UserDocument, String> {
    Optional<UserDocument> findByGoogleSubjectId(String googleSubjectId);
    Optional<UserDocument> findByEmail(String email);
}
