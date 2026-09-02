package org.example.chat.presentation.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatbotResponse {
    private String answer;
    private List<SourceDto> sources;
    private boolean hasContext;
}
