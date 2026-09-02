package org.example.chat.presentation.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SourceDto {
    private String id;
    private String category;
    private String question;
    private Double similarity;
}
