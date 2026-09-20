package org.example.chat.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor

public class ChatMessageRequest {
    private String content;
    private String sender;
    private String roomId;
    private LocalDateTime localDateTime;
}
