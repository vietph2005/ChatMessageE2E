package org.example.chat.domain.repository;

import org.example.chat.domain.model.HandshakeVerification;

import java.util.Optional;

public interface HandshakeRepository {
    HandshakeVerification save(HandshakeVerification handshake);
    Optional<HandshakeVerification> findByConversationId(String conversationId);
}
