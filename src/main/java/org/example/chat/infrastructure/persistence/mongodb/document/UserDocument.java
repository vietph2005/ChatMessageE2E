package org.example.chat.infrastructure.persistence.mongodb.document;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.HashSet;
import java.util.Set;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Document(collection = "users")
public class UserDocument {
    @Id
    private String id;

    @Indexed(unique = true)
    private String googleSubjectId;

    @Indexed(unique = true)
    private String email;

    private String displayName;
    private String avatarUrl;

    @Builder.Default
    private Set<String> blockedUserIds = new HashSet<>();

    private Instant createdAt;
    private Instant lastSeenAt;
    private boolean isOnline;
}
