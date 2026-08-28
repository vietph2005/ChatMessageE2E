package org.example.chat.infrastructure.persistence.mongodb.repository;

import org.example.chat.infrastructure.persistence.mongodb.document.EncryptedMessageDocument;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SpringDataMongoMessageRepository extends MongoRepository<EncryptedMessageDocument, String> {
    List<EncryptedMessageDocument> findByConversationIdOrderBySentAtAsc(String conversationId);
    int countByConversationId(String conversationId);
}
