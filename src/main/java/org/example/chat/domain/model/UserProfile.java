package org.example.chat.domain.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.HashSet;
import java.util.Set;

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

    @Builder.Default
    private Set<String> blockedUserIds = new HashSet<>();

    private Instant createdAt;
    private Instant lastSeenAt;
    private boolean isOnline;
}
