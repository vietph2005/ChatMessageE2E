package org.example.chat.presentation.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.example.chat.domain.model.UserPublicKeyBundle;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PublicKeyBundleDto {
    private String userId;

    @NotBlank(message = "Identity public key is required")
    private String identityPublicKey;

    @NotBlank(message = "Signed pre-key is required")
    private String signedPreKey;

    private String preKeySignature;
    private int keyVersion;

    public static PublicKeyBundleDto fromDomain(UserPublicKeyBundle bundle) {
        return PublicKeyBundleDto.builder()
                .userId(bundle.getUserId())
                .identityPublicKey(bundle.getIdentityPublicKey())
                .signedPreKey(bundle.getSignedPreKey())
                .preKeySignature(bundle.getPreKeySignature())
                .keyVersion(bundle.getKeyVersion())
                .build();
    }

    public UserPublicKeyBundle toDomain(String userId) {
        return UserPublicKeyBundle.builder()
                .userId(userId)
                .identityPublicKey(this.identityPublicKey)
                .signedPreKey(this.signedPreKey)
                .preKeySignature(this.preKeySignature)
                .keyVersion(this.keyVersion)
                .build();
    }
}
