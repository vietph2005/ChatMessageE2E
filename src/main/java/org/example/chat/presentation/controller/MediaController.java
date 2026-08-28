package org.example.chat.presentation.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.example.chat.domain.exception.DomainException;
import org.example.chat.infrastructure.security.ChatUserDetails;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@RestController
@RequestMapping("/api/v1/media")
@RequiredArgsConstructor
public class MediaController {

    // In-memory / temporary buffer for encrypted binary blobs (Zero-Knowledge)
    private final Map<String, byte[]> encryptedStorage = new ConcurrentHashMap<>();

    @PostMapping("/upload")
    public ResponseEntity<Map<String, String>> uploadEncryptedMedia(
            @AuthenticationPrincipal ChatUserDetails userDetails,
            @RequestParam("encryptedFile") MultipartFile file,
            @RequestParam("conversationId") String conversationId) {

        if (file.isEmpty()) {
            throw new DomainException("EMPTY_FILE", "Uploaded encrypted file is empty", HttpStatus.BAD_REQUEST);
        }

        if (file.getSize() > 5 * 1024 * 1024) {
            throw new DomainException("FILE_TOO_LARGE", "Encrypted media exceeds 5MB size limit", HttpStatus.BAD_REQUEST);
        }

        try {
            String mediaId = UUID.randomUUID().toString();
            encryptedStorage.put(mediaId, file.getBytes());

            String mediaUrl = "/api/v1/media/" + mediaId;
            log.info("[MediaService] Stored encrypted media blob: {} (Size: {} bytes)", mediaId, file.getSize());

            return ResponseEntity.status(HttpStatus.CREATED).body(Map.of(
                    "mediaId", mediaId,
                    "mediaUrl", mediaUrl
            ));
        } catch (IOException e) {
            log.error("Failed to store encrypted media", e);
            throw new DomainException("MEDIA_UPLOAD_FAILED", "Failed to store encrypted media blob", HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @GetMapping("/{mediaId}")
    public ResponseEntity<Resource> downloadEncryptedMedia(@PathVariable("mediaId") String mediaId) {
        byte[] data = encryptedStorage.get(mediaId);
        if (data == null) {
            throw new DomainException("MEDIA_NOT_FOUND", "Encrypted media blob not found", HttpStatus.NOT_FOUND);
        }

        ByteArrayResource resource = new ByteArrayResource(data);
        return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"encrypted_" + mediaId + ".bin\"")
                .body(resource);
    }
}
