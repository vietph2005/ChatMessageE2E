package org.example.chat.infrastructure.persistence.mongodb.document;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Document(collection = "user_public_keys")
public class UserPublicKeyDocument {
    @Id
    private String id;

    @Indexed(unique = true)
    private String userId;

    private String identityPublicKey;
    private String signedPreKey;
    private String preKeySignature;
    private int keyVersion;
    private Instant updatedAt;
}
