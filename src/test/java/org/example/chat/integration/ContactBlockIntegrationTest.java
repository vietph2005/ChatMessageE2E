package org.example.chat.integration;

import org.example.chat.application.service.UserService;
import org.example.chat.domain.model.Conversation;
import org.example.chat.domain.repository.ConversationRepository;
import org.example.chat.infrastructure.security.ChatUserDetails;
import org.example.chat.presentation.controller.BlockController;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.ResponseEntity;

import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ContactBlockIntegrationTest {

    @Mock
    private ConversationRepository conversationRepository;

    @Mock
    private UserService userService;

    @InjectMocks
    private BlockController blockController;

    @Test
    @DisplayName("Should block contact and update conversation status to BLOCKED")
    void testBlockUser() {
        ChatUserDetails user = new ChatUserDetails("user_alice", "alice@gmail.com");

        Conversation conv = Conversation.builder()
                .id("conv_101")
                .participantAId("user_alice")
                .participantBId("user_bob")
                .status(Conversation.ConversationStatus.VERIFIED_ACTIVE)
                .build();

        when(conversationRepository.findBetweenParticipants("user_alice", "user_bob")).thenReturn(Optional.of(conv));

        ResponseEntity<Void> response = blockController.blockUser(user, Map.of("userId", "user_bob"));

        assertEquals(200, response.getStatusCode().value());
        assertEquals(Conversation.ConversationStatus.BLOCKED, conv.getStatus());
        verify(userService).blockUser("user_alice", "user_bob");
        verify(conversationRepository).save(conv);
    }

    @Test
    @DisplayName("Should unblock contact and restore conversation status to VERIFIED_ACTIVE")
    void testUnblockUser() {
        ChatUserDetails user = new ChatUserDetails("user_alice", "alice@gmail.com");

        Conversation conv = Conversation.builder()
                .id("conv_101")
                .participantAId("user_alice")
                .participantBId("user_bob")
                .status(Conversation.ConversationStatus.BLOCKED)
                .build();

        when(conversationRepository.findBetweenParticipants("user_alice", "user_bob")).thenReturn(Optional.of(conv));

        ResponseEntity<Void> response = blockController.unblockUser(user, Map.of("userId", "user_bob"));

        assertEquals(200, response.getStatusCode().value());
        assertEquals(Conversation.ConversationStatus.VERIFIED_ACTIVE, conv.getStatus());
        verify(userService).unblockUser("user_alice", "user_bob");
        verify(conversationRepository).save(conv);
    }
}
