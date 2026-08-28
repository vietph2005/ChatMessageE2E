package org.example.chat.infrastructure.persistence.mongodb.repository;

import org.example.chat.infrastructure.persistence.mongodb.document.HandshakeVerificationDocument;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface SpringDataMongoHandshakeRepository extends MongoRepository<HandshakeVerificationDocument, String> {
    Optional<HandshakeVerificationDocument> findByConversationId(String conversationId);
}
