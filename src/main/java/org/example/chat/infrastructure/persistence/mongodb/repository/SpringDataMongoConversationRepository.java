package org.example.chat.infrastructure.persistence.mongodb.repository;

import org.example.chat.infrastructure.persistence.mongodb.document.ConversationDocument;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface SpringDataMongoConversationRepository extends MongoRepository<ConversationDocument, String> {

    @Query("{ $or: [ { 'participantAId': ?0, 'participantBId': ?1 }, { 'participantAId': ?1, 'participantBId': ?0 } ] }")
    Optional<ConversationDocument> findBetween(String userA, String userB);

    @Query(value = "{ $or: [ { 'participantAId': ?0 }, { 'participantBId': ?0 } ] }", sort = "{ 'lastMessageAt': -1 }")
    List<ConversationDocument> findByUser(String userId);
}
