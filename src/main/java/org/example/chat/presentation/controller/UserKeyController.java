package org.example.chat.presentation.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.example.chat.application.service.UserService;
import org.example.chat.domain.model.UserProfile;
import org.example.chat.domain.model.UserPublicKeyBundle;
import org.example.chat.infrastructure.security.ChatUserDetails;
import org.example.chat.presentation.dto.PublicKeyBundleDto;
import org.example.chat.presentation.dto.UserProfileDto;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserKeyController {

    private final UserService userService;

    @GetMapping("/search")
    public ResponseEntity<UserProfileDto> searchByExactGmail(@RequestParam("email") String email) {
        UserProfile user = userService.searchByExactGmail(email);
        return ResponseEntity.ok(UserProfileDto.fromDomain(user));
    }

    @PostMapping("/keys")
    public ResponseEntity<Void> registerPublicKeyBundle(
            @AuthenticationPrincipal ChatUserDetails userDetails,
            @Valid @RequestBody PublicKeyBundleDto dto) {
        userService.registerPublicKeyBundle(userDetails.getUserId(), dto.toDomain(userDetails.getUserId()));
        return ResponseEntity.ok().build();
    }

    @GetMapping("/keys")
    public ResponseEntity<PublicKeyBundleDto> getPublicKeyBundle(@RequestParam("userId") String userId) {
        UserPublicKeyBundle bundle = userService.getPublicKeyBundle(userId);
        return ResponseEntity.ok(PublicKeyBundleDto.fromDomain(bundle));
    }
}
