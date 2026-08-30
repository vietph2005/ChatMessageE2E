package org.example.chat.presentation.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.example.chat.application.service.UserService;
import org.example.chat.domain.repository.ConversationRepository;
import org.example.chat.infrastructure.security.ChatUserDetails;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class BlockController {

    private final ConversationRepository conversationRepository;
    private final UserService userService;

    @PostMapping("/block")
    public ResponseEntity<Void> blockUser(
            @AuthenticationPrincipal ChatUserDetails userDetails,
            @RequestBody Map<String, String> body) {
        String peerUserId = body.get("userId");
        if (peerUserId != null) {
            userService.blockUser(userDetails.getUserId(), peerUserId);
            conversationRepository.findBetweenParticipants(userDetails.getUserId(), peerUserId)
                    .ifPresent(conv -> {
                        conv.setStatus(org.example.chat.domain.model.Conversation.ConversationStatus.BLOCKED);
                        conversationRepository.save(conv);
                        log.info("[BlockController] User {} blocked conversation {}", userDetails.getUserId(), conv.getId());
                    });
        }
        return ResponseEntity.ok().build();
    }

    @PostMapping("/unblock")
    public ResponseEntity<Void> unblockUser(
            @AuthenticationPrincipal ChatUserDetails userDetails,
            @RequestBody Map<String, String> body) {
        String peerUserId = body.get("userId");
        if (peerUserId != null) {
            userService.unblockUser(userDetails.getUserId(), peerUserId);
            conversationRepository.findBetweenParticipants(userDetails.getUserId(), peerUserId)
                    .ifPresent(conv -> {
                        conv.setStatus(org.example.chat.domain.model.Conversation.ConversationStatus.VERIFIED_ACTIVE);
                        conversationRepository.save(conv);
                        log.info("[BlockController] User {} unblocked conversation {}", userDetails.getUserId(), conv.getId());
                    });
        }
        return ResponseEntity.ok().build();
    }
}
