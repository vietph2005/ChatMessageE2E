package org.example.chat.domain.repository;

import org.example.chat.domain.model.EncryptedMessage;

import java.util.List;
import java.util.Optional;

public interface MessageRepository {
    EncryptedMessage save(EncryptedMessage message);
    Optional<EncryptedMessage> findById(String id);
    List<EncryptedMessage> findByConversationIdOrderBySentAtAsc(String conversationId);
    int countByConversationId(String conversationId);
}
