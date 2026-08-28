package org.example.chat.infrastructure.persistence.mongodb.document;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.CompoundIndex;
import org.springframework.data.mongodb.core.index.CompoundIndexes;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Document(collection = "conversations")
@CompoundIndexes({
        @CompoundIndex(name = "participants_idx", def = "{'participantAId': 1, 'participantBId': 1}", unique = true)
})
public class ConversationDocument {
    @Id
    private String id;

    @Indexed
    private String participantAId;

    @Indexed
    private String participantBId;

    private String status;
    private String lastMessageId;
    private String lastMessageSnippet;

    @Indexed
    private Instant lastMessageAt;

    private Instant createdAt;
    private Instant updatedAt;
}
