package org.example.chat.presentation.websocket;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.example.chat.application.service.MessageService;
import org.example.chat.application.service.UserService;
import org.example.chat.domain.model.EncryptedMessage;
import org.example.chat.domain.model.UserProfile;
import org.example.chat.infrastructure.security.ChatUserDetails;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.messaging.simp.SimpMessageHeaderAccessor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.util.StringUtils;

import java.security.Principal;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@Controller
@RequiredArgsConstructor
public class ChatStompController {

    private final MessageService messageService;
    private final UserService userService;
    private final SimpMessagingTemplate messagingTemplate;

    @MessageMapping("/chat.send")
    public void handleSendMessage(
            Principal principal,
            SimpMessageHeaderAccessor headerAccessor,
            @Payload SendMessagePayload payload) {

        String senderId = resolveUserId(principal, headerAccessor, payload.senderId);

        if (!StringUtils.hasText(senderId)) {
            log.error("[STOMP] Unable to resolve sender ID for chat message in conversation {}", payload.conversationId);
            return;
        }

        EncryptedMessage.MessageType type = "IMAGE".equalsIgnoreCase(payload.messageType)
                ? EncryptedMessage.MessageType.IMAGE
                : EncryptedMessage.MessageType.TEXT;

        EncryptedMessage saved = messageService.sendEncryptedMessage(
                senderId,
                payload.conversationId,
                payload.recipientId,
                type,
                payload.ciphertext,
                payload.initializationVector,
                payload.mediaUrl
        );

        // Broadcast encrypted payload to conversation participants
        Map<String, Object> broadcastPayload = new HashMap<>();
        broadcastPayload.put("messageId", saved.getId());
        broadcastPayload.put("conversationId", saved.getConversationId());
        broadcastPayload.put("senderId", saved.getSenderId());
        broadcastPayload.put("recipientId", saved.getRecipientId());
        broadcastPayload.put("messageType", saved.getMessageType().name());
        broadcastPayload.put("ciphertext", saved.getCiphertext());
        broadcastPayload.put("initializationVector", saved.getInitializationVector());
        broadcastPayload.put("mediaUrl", saved.getMediaUrl());
        broadcastPayload.put("sequenceNumber", saved.getSequenceNumber());
        broadcastPayload.put("sentAt", saved.getSentAt().toString());
        broadcastPayload.put("isRevoked", false);

        String destination = "/topic/conversation/" + payload.conversationId;
        messagingTemplate.convertAndSend(destination, broadcastPayload);
        log.debug("[STOMP] Broadcasted encrypted message to {}", destination);
    }

    @MessageMapping("/chat.typing")
    public void handleTyping(
            Principal principal,
            SimpMessageHeaderAccessor headerAccessor,
            @Payload TypingPayload payload) {

        String userId = resolveUserId(principal, headerAccessor, null);

        Map<String, Object> event = new HashMap<>();
        event.put("conversationId", payload.conversationId);
        event.put("userId", userId);
        event.put("isTyping", payload.isTyping);

        messagingTemplate.convertAndSend("/topic/conversation/" + payload.conversationId + "/typing", event);
    }

    @MessageMapping("/chat.unsend")
    public void handleUnsend(
            Principal principal,
            SimpMessageHeaderAccessor headerAccessor,
            @Payload UnsendPayload payload) {

        String userId = resolveUserId(principal, headerAccessor, null);

        EncryptedMessage revoked = messageService.revokeMessage(userId, payload.conversationId, payload.messageId);

        Map<String, Object> event = new HashMap<>();
        event.put("messageId", revoked.getId());
        event.put("conversationId", revoked.getConversationId());
        event.put("revokedBy", userId);
        event.put("revokedAt", revoked.getRevokedAt() != null ? revoked.getRevokedAt().toString() : Instant.now().toString());

        messagingTemplate.convertAndSend("/topic/conversation/" + payload.conversationId + "/revocations", event);
    }

    private String resolveUserId(Principal principal, SimpMessageHeaderAccessor headerAccessor, String fallbackId) {
        // 1. Try Principal
        if (principal instanceof Authentication auth) {
            if (auth.getPrincipal() instanceof ChatUserDetails details) {
                return details.getUserId();
            }
        }

        // 2. Try SimpMessageHeaderAccessor User
        if (headerAccessor != null && headerAccessor.getUser() instanceof Authentication auth) {
            if (auth.getPrincipal() instanceof ChatUserDetails details) {
                return details.getUserId();
            }
        }

        // 3. Try Principal Name (might be email)
        if (principal != null && StringUtils.hasText(principal.getName())) {
            try {
                UserProfile user = userService.searchByExactGmail(principal.getName());
                return user.getId();
            } catch (Exception ignored) {}
        }

        // 4. Fallback from payload
        return fallbackId;
    }

    public record SendMessagePayload(
            String conversationId,
            String senderId,
            String recipientId,
            String messageType,
            String ciphertext,
            String initializationVector,
            String mediaUrl,
            String clientSentAt
    ) {}

    public record TypingPayload(String conversationId, boolean isTyping) {}

    public record UnsendPayload(String conversationId, String messageId) {}
}
