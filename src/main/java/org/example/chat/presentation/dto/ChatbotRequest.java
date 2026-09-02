package org.example.chat.presentation.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatbotRequest {
    @NotBlank(message = "Question must not be blank")
    @Size(max = 1000, message = "Question must be at most 1000 characters")
    private String question;
}
