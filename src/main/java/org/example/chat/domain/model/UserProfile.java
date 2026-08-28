package org.example.chat.domain.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserProfile {
    private String id;
    private String googleSubjectId;
    private String email;
    private String displayName;
    private String avatarUrl;
    private Instant createdAt;
    private Instant lastSeenAt;
    private boolean isOnline;
}
