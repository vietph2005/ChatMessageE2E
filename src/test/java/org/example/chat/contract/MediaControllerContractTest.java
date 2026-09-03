package org.example.chat.contract;

import org.example.chat.infrastructure.security.JwtTokenProvider;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class MediaControllerContractTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private JwtTokenProvider jwtTokenProvider;

    @Test
    @DisplayName("Contract: POST /api/v1/media/upload and GET /api/v1/media/{id}")
    void testMediaUploadAndDownload() throws Exception {
        String token = jwtTokenProvider.generateToken("user_alice", "alice@gmail.com", "Alice");

        MockMultipartFile file = new MockMultipartFile(
                "encryptedFile",
                "encrypted_image.bin",
                "application/octet-stream",
                "ENCRYPTED_IMAGE_BINARY_BLOB".getBytes()
        );

        MvcResult uploadResult = mockMvc.perform(multipart("/api/v1/media/upload")
                        .file(file)
                        .param("conversationId", "conv_123")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.mediaId").isNotEmpty())
                .andExpect(jsonPath("$.mediaUrl").isNotEmpty())
                .andReturn();

        String responseJson = uploadResult.getResponse().getContentAsString();
        String mediaId = com.jayway.jsonpath.JsonPath.read(responseJson, "$.mediaId");
        assertNotNull(mediaId);

        // Download media
        mockMvc.perform(get("/api/v1/media/" + mediaId)
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_OCTET_STREAM))
                .andExpect(content().bytes("ENCRYPTED_IMAGE_BINARY_BLOB".getBytes()));
    }

    @Test
    @DisplayName("Contract: Upload empty file should return 400 Bad Request")
    void testEmptyFileUpload() throws Exception {
        String token = jwtTokenProvider.generateToken("user_alice", "alice@gmail.com", "Alice");

        MockMultipartFile emptyFile = new MockMultipartFile(
                "encryptedFile",
                "empty.bin",
                "application/octet-stream",
                new byte[0]
        );

        mockMvc.perform(multipart("/api/v1/media/upload")
                        .file(emptyFile)
                        .param("conversationId", "conv_123")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.errorCode").value("EMPTY_FILE"));
    }

    @Test
    @DisplayName("Contract: Download non-existent media should return 404 Not Found")
    void testDownloadNonExistentMedia() throws Exception {
        String token = jwtTokenProvider.generateToken("user_alice", "alice@gmail.com", "Alice");

        mockMvc.perform(get("/api/v1/media/non_existent_id")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.errorCode").value("MEDIA_NOT_FOUND"));
    }
}
