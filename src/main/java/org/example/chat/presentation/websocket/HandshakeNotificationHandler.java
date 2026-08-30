package org.example.chat.presentation.websocket;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.example.chat.domain.model.UserProfile;
import org.example.chat.presentation.dto.UserProfileDto;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class HandshakeNotificationHandler {

    private final SimpMessagingTemplate messagingTemplate;

    public void notifyInvitationReceived(String recipientUserId, String conversationId, UserProfile initiator) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("eventType", "HANDSHAKE_INVITATION_RECEIVED");
        payload.put("conversationId", conversationId);
        payload.put("initiator", UserProfileDto.fromDomain(initiator));
        payload.put("timestamp", Instant.now().toString());

        log.info("[WebSocket Notification] Pushing invitation event to user: {}", recipientUserId);
        messagingTemplate.convertAndSendToUser(recipientUserId, "/queue/notifications", payload);
    }

    public void notifyHandshakeAccepted(String userId, String conversationId, String safetyCode) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("eventType", "HANDSHAKE_ACCEPTED");
        payload.put("conversationId", conversationId);
        payload.put("safetyCode", safetyCode);
        payload.put("timestamp", Instant.now().toString());

        messagingTemplate.convertAndSendToUser(userId, "/queue/notifications", payload);
    }

    public void notifySafetyCodeConfirmed(String userId, String conversationId) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("eventType", "SAFETY_CODE_CONFIRMED");
        payload.put("conversationId", conversationId);
        payload.put("timestamp", Instant.now().toString());

        messagingTemplate.convertAndSendToUser(userId, "/queue/notifications", payload);
    }

    public void notifyKeyChanged(String recipientUserId, String conversationId, UserProfile initiator) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("eventType", "KEY_CHANGED");
        payload.put("conversationId", conversationId);
        payload.put("initiator", UserProfileDto.fromDomain(initiator));
        payload.put("timestamp", Instant.now().toString());

        log.info("[WebSocket Notification] Pushing key changed event to user: {}", recipientUserId);
        messagingTemplate.convertAndSendToUser(recipientUserId, "/queue/notifications", payload);
    }
}
