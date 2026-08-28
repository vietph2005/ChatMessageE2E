package org.example.chat.contract;

import org.example.chat.application.service.MessageService;
import org.example.chat.domain.model.EncryptedMessage;
import org.example.chat.infrastructure.security.ChatUserDetails;
import org.example.chat.presentation.websocket.ChatStompController;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;

import java.time.Instant;
import java.util.Collections;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class WebSocketMessageContractTest {

    @Mock
    private MessageService messageService;

    @Mock
    private SimpMessagingTemplate messagingTemplate;

    @InjectMocks
    private ChatStompController chatStompController;

    @Test
    @DisplayName("Contract: STOMP /app/chat.send persists and broadcasts to /topic/conversation/{id}")
    void shouldHandleSendMessage() {
        ChatUserDetails user = new ChatUserDetails("user_alice", "alice@gmail.com");
        UsernamePasswordAuthenticationToken auth = new UsernamePasswordAuthenticationToken(user, null, Collections.emptyList());

        ChatStompController.SendMessagePayload payload = new ChatStompController.SendMessagePayload(
                "conv_123",
                "user_alice",
                "user_bob",
                "TEXT",
                "encrypted_ciphertext_payload",
                "iv_base64",
                null,
                Instant.now().toString()
        );

        EncryptedMessage savedMessage = EncryptedMessage.builder()
                .id("msg_789")
                .conversationId("conv_123")
                .senderId("user_alice")
                .recipientId("user_bob")
                .messageType(EncryptedMessage.MessageType.TEXT)
                .ciphertext("encrypted_ciphertext_payload")
                .initializationVector("iv_base64")
                .sequenceNumber(1)
                .sentAt(Instant.now())
                .isRevoked(false)
                .build();

        when(messageService.sendEncryptedMessage(
                eq("user_alice"), eq("conv_123"), eq("user_bob"),
                eq(EncryptedMessage.MessageType.TEXT), any(), any(), any()
        )).thenReturn(savedMessage);

        chatStompController.handleSendMessage(auth, null, payload);

        verify(messagingTemplate).convertAndSend(eq("/topic/conversation/conv_123"), any(Object.class));
    }
}
