package org.example.chat.presentation.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.example.chat.domain.model.Conversation;
import org.example.chat.domain.model.HandshakeVerification;

import java.time.Instant;

public class ConversationDto {

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class InitiateRequest {
        @NotBlank(message = "Recipient email is required")
        private String recipientEmail;

        @NotBlank(message = "Initiator public key is required")
        private String initiatorPublicKey;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class AcceptRequest {
        @NotBlank(message = "Recipient public key is required")
        private String recipientPublicKey;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ConfirmSafetyCodeRequest {
        @NotBlank(message = "Safety code is required")
        private String safetyCode;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ConversationSummaryResponse {
        private String id;
        private UserProfileDto peerUser;
        private String status;
        private String lastMessageSnippet;
        private Instant lastMessageAt;
        private int unreadCount;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ConversationDetailResponse {
        private String id;
        private String participantAId;
        private String participantBId;
        private String status;
        private HandshakeStateDto handshake;

        public static ConversationDetailResponse fromDomain(Conversation c, HandshakeVerification h) {
            return ConversationDetailResponse.builder()
                    .id(c.getId())
                    .participantAId(c.getParticipantAId())
                    .participantBId(c.getParticipantBId())
                    .status(c.getStatus().name())
                    .handshake(h != null ? HandshakeStateDto.fromDomain(h) : null)
                    .build();
        }
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class HandshakeStateDto {
        private String layer1Status;
        private String layer2Status;
        private String layer3Status;
        private String layer4Status;
        private String safetyCode;
        private String fullFingerprintHex;

        public static HandshakeStateDto fromDomain(HandshakeVerification h) {
            return HandshakeStateDto.builder()
                    .layer1Status(h.getLayer1Status() != null ? h.getLayer1Status().name() : null)
                    .layer2Status(h.getLayer2Status() != null ? h.getLayer2Status().name() : null)
                    .layer3Status(h.getLayer3Status() != null ? h.getLayer3Status().name() : null)
                    .layer4Status(h.getLayer4Status() != null ? h.getLayer4Status().name() : null)
                    .safetyCode(h.getSafetyCode())
                    .fullFingerprintHex(h.getFullFingerprintHex())
                    .build();
        }
    }
}
