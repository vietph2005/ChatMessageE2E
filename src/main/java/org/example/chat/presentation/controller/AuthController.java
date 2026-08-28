package org.example.chat.presentation.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.example.chat.application.service.UserService;
import org.example.chat.presentation.dto.AuthDto;
import org.example.chat.presentation.dto.UserProfileDto;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {

    private final UserService userService;

    @PostMapping("/google")
    public ResponseEntity<AuthDto.AuthResponse> authenticateWithGoogle(@Valid @RequestBody AuthDto.GoogleAuthRequest request) {
        UserService.AuthResult result = userService.authenticateWithGoogle(request.getIdToken());
        AuthDto.AuthResponse response = AuthDto.AuthResponse.builder()
                .accessToken(result.accessToken())
                .expiresIn(result.expiresIn())
                .user(UserProfileDto.fromDomain(result.user()))
                .build();
        return ResponseEntity.ok(response);
    }
}
