package org.example.chat.domain.repository;

import org.example.chat.domain.model.Conversation;

import java.util.List;
import java.util.Optional;

public interface ConversationRepository {
    Conversation save(Conversation conversation);
    Optional<Conversation> findById(String id);
    Optional<Conversation> findBetweenParticipants(String participantAId, String participantBId);
    List<Conversation> findUserConversations(String userId);
}
