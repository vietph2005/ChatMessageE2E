package org.example.chat.presentation.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.example.chat.application.service.HandshakeService;
import org.example.chat.application.service.UserService;
import org.example.chat.domain.model.Conversation;
import org.example.chat.domain.model.HandshakeVerification;
import org.example.chat.domain.model.UserProfile;
import org.example.chat.domain.repository.ConversationRepository;
import org.example.chat.infrastructure.security.ChatUserDetails;
import org.example.chat.presentation.dto.ConversationDto;
import org.example.chat.presentation.dto.UserProfileDto;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/conversations")
@RequiredArgsConstructor
public class ConversationController {

    private final ConversationRepository conversationRepository;
    private final HandshakeService handshakeService;
    private final UserService userService;

    @GetMapping
    public ResponseEntity<List<ConversationDto.ConversationSummaryResponse>> listConversations(
            @AuthenticationPrincipal ChatUserDetails userDetails) {
        List<Conversation> conversations = conversationRepository.findUserConversations(userDetails.getUserId());

        List<ConversationDto.ConversationSummaryResponse> summaries = conversations.stream().map(c -> {
            String peerId = c.getParticipantAId().equals(userDetails.getUserId())
                    ? c.getParticipantBId()
                    : c.getParticipantAId();

            UserProfile peerUser = userService.getUserById(peerId);

            return ConversationDto.ConversationSummaryResponse.builder()
                    .id(c.getId())
                    .peerUser(UserProfileDto.fromDomain(peerUser))
                    .status(c.getStatus().name())
                    .lastMessageSnippet(c.getLastMessageSnippet())
                    .lastMessageAt(c.getLastMessageAt())
                    .unreadCount(0)
                    .build();
        }).collect(Collectors.toList());

        return ResponseEntity.ok(summaries);
    }

    @PostMapping
    public ResponseEntity<ConversationDto.ConversationDetailResponse> initiateConversation(
            @AuthenticationPrincipal ChatUserDetails userDetails,
            @Valid @RequestBody ConversationDto.InitiateRequest request) {
        Conversation conversation = handshakeService.initiateHandshake(
                userDetails.getUserId(),
                request.getRecipientEmail(),
                request.getInitiatorPublicKey()
        );
        HandshakeVerification handshake = handshakeService.getHandshake(conversation.getId());
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ConversationDto.ConversationDetailResponse.fromDomain(conversation, handshake));
    }

    @PostMapping("/{id}/handshake/accept")
    public ResponseEntity<ConversationDto.ConversationDetailResponse> acceptHandshake(
            @AuthenticationPrincipal ChatUserDetails userDetails,
            @PathVariable("id") String conversationId,
            @Valid @RequestBody ConversationDto.AcceptRequest request) {
        HandshakeVerification handshake = handshakeService.acceptHandshake(
                userDetails.getUserId(),
                conversationId,
                request.getRecipientPublicKey()
        );
        Conversation conversation = conversationRepository.findById(conversationId).orElseThrow();
        return ResponseEntity.ok(ConversationDto.ConversationDetailResponse.fromDomain(conversation, handshake));
    }

    @PostMapping("/{id}/handshake/confirm-safety-code")
    public ResponseEntity<ConversationDto.ConversationDetailResponse> confirmSafetyCode(
            @AuthenticationPrincipal ChatUserDetails userDetails,
            @PathVariable("id") String conversationId,
            @Valid @RequestBody ConversationDto.ConfirmSafetyCodeRequest request) {
        Conversation conversation = handshakeService.confirmSafetyCode(
                userDetails.getUserId(),
                conversationId,
                request.getSafetyCode()
        );
        HandshakeVerification handshake = handshakeService.getHandshake(conversation.getId());
        return ResponseEntity.ok(ConversationDto.ConversationDetailResponse.fromDomain(conversation, handshake));
    }

    @PostMapping("/{id}/handshake/re-initiate")
    public ResponseEntity<ConversationDto.ConversationDetailResponse> reInitiateHandshake(
            @AuthenticationPrincipal ChatUserDetails userDetails,
            @PathVariable("id") String conversationId,
            @Valid @RequestBody ConversationDto.ReInitiateRequest request) {
        HandshakeVerification handshake = handshakeService.reInitiateHandshake(
                userDetails.getUserId(),
                conversationId,
                request.getInitiatorPublicKey()
        );
        Conversation conversation = conversationRepository.findById(conversationId).orElseThrow();
        return ResponseEntity.ok(ConversationDto.ConversationDetailResponse.fromDomain(conversation, handshake));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ConversationDto.ConversationDetailResponse> getConversationDetail(
            @PathVariable("id") String conversationId) {
        Conversation conversation = conversationRepository.findById(conversationId).orElseThrow();
        HandshakeVerification handshake = handshakeService.getHandshake(conversationId);
        return ResponseEntity.ok(ConversationDto.ConversationDetailResponse.fromDomain(conversation, handshake));
    }
}
