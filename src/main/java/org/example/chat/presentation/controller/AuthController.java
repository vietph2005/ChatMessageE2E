package org.example.chat.presentation.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.example.chat.application.service.UserService;
import org.example.chat.domain.model.UserProfile;
import org.example.chat.infrastructure.security.ChatUserDetails;
import org.example.chat.presentation.dto.AuthDto;
import org.example.chat.presentation.dto.UserProfileDto;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseCookie;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

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

        ResponseCookie cookie = ResponseCookie.from("ACCESS_TOKEN", result.accessToken())
                .httpOnly(true)
                .secure(false)
                .path("/")
                .maxAge(86400)
                .sameSite("Lax")
                .build();

        return ResponseEntity.ok()
                .header(HttpHeaders.SET_COOKIE, cookie.toString())
                .body(response);
    }

    @GetMapping("/me")
    public ResponseEntity<UserProfileDto> getCurrentUser(@AuthenticationPrincipal ChatUserDetails userDetails) {
        if (userDetails == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }
        UserProfile user = userService.getUserById(userDetails.getUserId());
        return ResponseEntity.ok(UserProfileDto.fromDomain(user));
    }

    @PostMapping("/logout")
    public ResponseEntity<Void> logout() {
        ResponseCookie cookie = ResponseCookie.from("ACCESS_TOKEN", "")
                .httpOnly(true)
                .secure(false)
                .path("/")
                .maxAge(0)
                .sameSite("Lax")
                .build();

        return ResponseEntity.ok()
                .header(HttpHeaders.SET_COOKIE, cookie.toString())
                .build();
    }
}

