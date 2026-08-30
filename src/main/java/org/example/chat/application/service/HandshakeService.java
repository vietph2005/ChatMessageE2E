package org.example.chat.application.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.example.chat.domain.exception.DomainException;
import org.example.chat.domain.model.Conversation;
import org.example.chat.domain.model.HandshakeVerification;
import org.example.chat.domain.model.UserProfile;
import org.example.chat.domain.repository.ConversationRepository;
import org.example.chat.domain.repository.HandshakeRepository;
import org.example.chat.domain.repository.UserRepository;
import org.example.chat.presentation.websocket.HandshakeNotificationHandler;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Arrays;

@Slf4j
@Service
@RequiredArgsConstructor
public class HandshakeService {

    private final ConversationRepository conversationRepository;
    private final HandshakeRepository handshakeRepository;
    private final UserRepository userRepository;
    private final HandshakeNotificationHandler notificationHandler;

    public Conversation initiateHandshake(String initiatorId, String recipientEmail, String initiatorPublicKey) {
        UserProfile recipient = userRepository.findByEmail(recipientEmail.toLowerCase().trim())
                .orElseThrow(() -> new DomainException("USER_NOT_FOUND", "Recipient Gmail not registered on platform", HttpStatus.NOT_FOUND));

        if (initiatorId.equals(recipient.getId())) {
            throw new DomainException("INVALID_INITIATION", "Cannot initiate 1-1 conversation with yourself", HttpStatus.BAD_REQUEST);
        }

        UserProfile initiator = userRepository.findById(initiatorId)
                .orElseThrow(() -> new DomainException("USER_NOT_FOUND", "Initiator not found", HttpStatus.NOT_FOUND));

        // Check if conversation already exists between this pair
        return conversationRepository.findBetweenParticipants(initiatorId, recipient.getId())
                .orElseGet(() -> {
                    // Create Conversation
                    Conversation conversation = Conversation.builder()
                            .participantAId(initiatorId)
                            .participantBId(recipient.getId())
                            .status(Conversation.ConversationStatus.PENDING_ACCEPTANCE)
                            .createdAt(Instant.now())
                            .updatedAt(Instant.now())
                            .build();
                    Conversation savedConv = conversationRepository.save(conversation);

                    // Create Handshake Verification Record
                    HandshakeVerification handshake = HandshakeVerification.builder()
                            .conversationId(savedConv.getId())
                            .initiatorId(initiatorId)
                            .recipientId(recipient.getId())
                            .initiatorPublicKey(initiatorPublicKey)
                            .layer1Status(HandshakeVerification.LayerStatus.VERIFIED)
                            .layer1VerifiedAt(Instant.now())
                            .layer2Status(HandshakeVerification.LayerStatus.PENDING)
                            .layer3Status(HandshakeVerification.LayerStatus.PENDING)
                            .layer4Status(HandshakeVerification.LayerStatus.PENDING)
                            .build();
                    handshakeRepository.save(handshake);

                    log.info("[Handshake] Conversation initiated: {} between {} and {}",
                            savedConv.getId(), initiator.getEmail(), recipient.getEmail());

                    // Push notification to recipient (asynchronous delivery)
                    notificationHandler.notifyInvitationReceived(recipient.getId(), savedConv.getId(), initiator);

                    return savedConv;
                });
    }

    public HandshakeVerification acceptHandshake(String recipientId, String conversationId, String recipientPublicKey) {
        Conversation conversation = conversationRepository.findById(conversationId)
                .orElseThrow(() -> new DomainException("CONVERSATION_NOT_FOUND", "Conversation not found", HttpStatus.NOT_FOUND));

        if (!recipientId.equals(conversation.getParticipantBId()) && !recipientId.equals(conversation.getParticipantAId())) {
            throw new DomainException("UNAUTHORIZED_ACTION", "You are not a participant in this conversation", HttpStatus.FORBIDDEN);
        }

        HandshakeVerification handshake = handshakeRepository.findByConversationId(conversationId)
                .orElseThrow(() -> new DomainException("HANDSHAKE_NOT_FOUND", "Handshake record not found", HttpStatus.NOT_FOUND));

        // Layer 2: Consent
        handshake.setLayer2Status(HandshakeVerification.LayerStatus.ACCEPTED);
        handshake.setLayer2AcceptedAt(Instant.now());

        // Layer 3: Key exchange
        handshake.setRecipientPublicKey(recipientPublicKey);
        handshake.setLayer3Status(HandshakeVerification.LayerStatus.EXCHANGED);
        handshake.setLayer3ExchangedAt(Instant.now());

        // Layer 4: Compute deterministic 6-digit safety code and fingerprint
        SafetyCodeCalculated result = computeDeterministicSafetyCode(
                handshake.getInitiatorPublicKey(),
                handshake.getRecipientPublicKey(),
                conversationId
        );
        handshake.setSafetyCode(result.safetyCode());
        handshake.setFullFingerprintHex(result.fullFingerprintHex());
        handshake.setLayer4Status(HandshakeVerification.LayerStatus.PENDING);

        conversation.setStatus(Conversation.ConversationStatus.HANDSHAKE_IN_PROGRESS);
        conversation.setUpdatedAt(Instant.now());
        conversationRepository.save(conversation);

        HandshakeVerification savedHandshake = handshakeRepository.save(handshake);

        // Push event to both participants
        notificationHandler.notifyHandshakeAccepted(handshake.getInitiatorId(), conversationId, result.safetyCode());
        notificationHandler.notifyHandshakeAccepted(handshake.getRecipientId(), conversationId, result.safetyCode());

        return savedHandshake;
    }

    public Conversation confirmSafetyCode(String userId, String conversationId, String safetyCode) {
        Conversation conversation = conversationRepository.findById(conversationId)
                .orElseThrow(() -> new DomainException("CONVERSATION_NOT_FOUND", "Conversation not found", HttpStatus.NOT_FOUND));

        HandshakeVerification handshake = handshakeRepository.findByConversationId(conversationId)
                .orElseThrow(() -> new DomainException("HANDSHAKE_NOT_FOUND", "Handshake record not found", HttpStatus.NOT_FOUND));

        if (!safetyCode.trim().equals(handshake.getSafetyCode())) {
            throw new DomainException("SAFETY_CODE_MISMATCH", "Provided safety code does not match expected cryptographic challenge", HttpStatus.BAD_REQUEST);
        }

        handshake.setLayer4Status(HandshakeVerification.LayerStatus.CONFIRMED);
        handshake.setLayer4ConfirmedAt(Instant.now());
        handshake.setCompletedAt(Instant.now());
        handshakeRepository.save(handshake);

        conversation.setStatus(Conversation.ConversationStatus.VERIFIED_ACTIVE);
        conversation.setUpdatedAt(Instant.now());
        Conversation savedConv = conversationRepository.save(conversation);

        log.info("[Handshake] Conversation verified and active: {}", conversationId);

        // Push event to active WebSocket channels
        notificationHandler.notifySafetyCodeConfirmed(conversation.getParticipantAId(), conversationId);
        notificationHandler.notifySafetyCodeConfirmed(conversation.getParticipantBId(), conversationId);

        return savedConv;
    }

    public HandshakeVerification reInitiateHandshake(String userId, String conversationId, String newPublicKey) {
        Conversation conversation = conversationRepository.findById(conversationId)
                .orElseThrow(() -> new DomainException("CONVERSATION_NOT_FOUND", "Conversation not found", HttpStatus.NOT_FOUND));

        if (!userId.equals(conversation.getParticipantAId()) && !userId.equals(conversation.getParticipantBId())) {
            throw new DomainException("UNAUTHORIZED_ACTION", "You are not a participant in this conversation", HttpStatus.FORBIDDEN);
        }

        UserProfile currentUser = userRepository.findById(userId)
                .orElseThrow(() -> new DomainException("USER_NOT_FOUND", "User not found", HttpStatus.NOT_FOUND));

        String peerId = userId.equals(conversation.getParticipantAId())
                ? conversation.getParticipantBId()
                : conversation.getParticipantAId();

        HandshakeVerification handshake = handshakeRepository.findByConversationId(conversationId)
                .orElseGet(() -> HandshakeVerification.builder()
                        .conversationId(conversationId)
                        .initiatorId(conversation.getParticipantAId())
                        .recipientId(conversation.getParticipantBId())
                        .build());

        if (userId.equals(handshake.getInitiatorId())) {
            handshake.setInitiatorPublicKey(newPublicKey);
        } else {
            handshake.setRecipientPublicKey(newPublicKey);
        }

        handshake.setLayer1Status(HandshakeVerification.LayerStatus.VERIFIED);
        handshake.setLayer1VerifiedAt(Instant.now());
        handshake.setLayer2Status(HandshakeVerification.LayerStatus.PENDING);
        handshake.setLayer2AcceptedAt(null);
        handshake.setLayer3Status(HandshakeVerification.LayerStatus.PENDING);
        handshake.setLayer3ExchangedAt(null);
        handshake.setLayer4Status(HandshakeVerification.LayerStatus.PENDING);
        handshake.setLayer4ConfirmedAt(null);
        handshake.setSafetyCode(null);
        handshake.setFullFingerprintHex(null);
        handshake.setVersion(handshake.getVersion() == null ? 2 : handshake.getVersion() + 1);

        conversation.setStatus(Conversation.ConversationStatus.HANDSHAKE_IN_PROGRESS);
        conversation.setUpdatedAt(Instant.now());
        conversationRepository.save(conversation);

        HandshakeVerification savedHandshake = handshakeRepository.save(handshake);

        log.info("[Handshake] Re-handshake initiated for conversation: {} by user: {}", conversationId, userId);
        notificationHandler.notifyKeyChanged(peerId, conversationId, currentUser);

        return savedHandshake;
    }

    public HandshakeVerification getHandshake(String conversationId) {
        return handshakeRepository.findByConversationId(conversationId)
                .orElseThrow(() -> new DomainException("HANDSHAKE_NOT_FOUND", "Handshake record not found", HttpStatus.NOT_FOUND));
    }

    private SafetyCodeCalculated computeDeterministicSafetyCode(String keyA, String keyB, String convId) {
        try {
            String[] sortedKeys = new String[]{keyA != null ? keyA : "", keyB != null ? keyB : ""};
            Arrays.sort(sortedKeys);
            String input = sortedKeys[0] + ":" + sortedKeys[1] + ":" + convId;

            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(input.getBytes(StandardCharsets.UTF_8));

            StringBuilder hex = new StringBuilder();
            for (byte b : hash) {
                hex.append(String.format("%02x", b));
            }

            int num = Math.abs(((hash[0] & 0xFF) << 24) |
                    ((hash[1] & 0xFF) << 16) |
                    ((hash[2] & 0xFF) << 8) |
                    (hash[3] & 0xFF)) % 1000000;

            String safetyCode = String.format("%06d", num);

            return new SafetyCodeCalculated(safetyCode, hex.toString());
        } catch (Exception e) {
            log.error("Failed to compute safety code", e);
            return new SafetyCodeCalculated("123456", "default_fingerprint");
        }
    }

    private record SafetyCodeCalculated(String safetyCode, String fullFingerprintHex) {}
}
