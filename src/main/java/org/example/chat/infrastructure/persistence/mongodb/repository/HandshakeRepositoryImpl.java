package org.example.chat.infrastructure.persistence.mongodb.repository;

import lombok.RequiredArgsConstructor;
import org.example.chat.domain.model.HandshakeVerification;
import org.example.chat.domain.repository.HandshakeRepository;
import org.example.chat.infrastructure.persistence.mongodb.document.HandshakeVerificationDocument;
import org.springframework.stereotype.Component;

import java.util.Optional;

@Component
@RequiredArgsConstructor
public class HandshakeRepositoryImpl implements HandshakeRepository {

    private final SpringDataMongoHandshakeRepository mongoRepository;

    @Override
    public HandshakeVerification save(HandshakeVerification h) {
        HandshakeVerificationDocument doc = toDocument(h);
        HandshakeVerificationDocument saved = mongoRepository.save(doc);
        return toDomain(saved);
    }

    @Override
    public Optional<HandshakeVerification> findByConversationId(String conversationId) {
        return mongoRepository.findByConversationId(conversationId).map(this::toDomain);
    }

    private HandshakeVerificationDocument toDocument(HandshakeVerification h) {
        return HandshakeVerificationDocument.builder()
                .id(h.getId())
                .conversationId(h.getConversationId())
                .initiatorId(h.getInitiatorId())
                .recipientId(h.getRecipientId())
                .initiatorPublicKey(h.getInitiatorPublicKey())
                .recipientPublicKey(h.getRecipientPublicKey())
                .layer1Status(h.getLayer1Status() != null ? h.getLayer1Status().name() : null)
                .layer2Status(h.getLayer2Status() != null ? h.getLayer2Status().name() : null)
                .layer3Status(h.getLayer3Status() != null ? h.getLayer3Status().name() : null)
                .layer4Status(h.getLayer4Status() != null ? h.getLayer4Status().name() : null)
                .safetyCode(h.getSafetyCode())
                .fullFingerprintHex(h.getFullFingerprintHex())
                .layer1VerifiedAt(h.getLayer1VerifiedAt())
                .layer2AcceptedAt(h.getLayer2AcceptedAt())
                .layer3ExchangedAt(h.getLayer3ExchangedAt())
                .layer4ConfirmedAt(h.getLayer4ConfirmedAt())
                .completedAt(h.getCompletedAt())
                .build();
    }

    private HandshakeVerification toDomain(HandshakeVerificationDocument doc) {
        return HandshakeVerification.builder()
                .id(doc.getId())
                .conversationId(doc.getConversationId())
                .initiatorId(doc.getInitiatorId())
                .recipientId(doc.getRecipientId())
                .initiatorPublicKey(doc.getInitiatorPublicKey())
                .recipientPublicKey(doc.getRecipientPublicKey())
                .layer1Status(doc.getLayer1Status() != null ? HandshakeVerification.LayerStatus.valueOf(doc.getLayer1Status()) : null)
                .layer2Status(doc.getLayer2Status() != null ? HandshakeVerification.LayerStatus.valueOf(doc.getLayer2Status()) : null)
                .layer3Status(doc.getLayer3Status() != null ? HandshakeVerification.LayerStatus.valueOf(doc.getLayer3Status()) : null)
                .layer4Status(doc.getLayer4Status() != null ? HandshakeVerification.LayerStatus.valueOf(doc.getLayer4Status()) : null)
                .safetyCode(doc.getSafetyCode())
                .fullFingerprintHex(doc.getFullFingerprintHex())
                .layer1VerifiedAt(doc.getLayer1VerifiedAt())
                .layer2AcceptedAt(doc.getLayer2AcceptedAt())
                .layer3ExchangedAt(doc.getLayer3ExchangedAt())
                .layer4ConfirmedAt(doc.getLayer4ConfirmedAt())
                .completedAt(doc.getCompletedAt())
                .build();
    }
}
