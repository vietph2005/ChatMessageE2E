package org.example.chat.infrastructure.persistence.mongodb.repository;

import lombok.RequiredArgsConstructor;
import org.example.chat.domain.model.UserPublicKeyBundle;
import org.example.chat.domain.repository.UserPublicKeyRepository;
import org.example.chat.infrastructure.persistence.mongodb.document.UserPublicKeyDocument;
import org.springframework.stereotype.Component;

import java.util.Optional;

@Component
@RequiredArgsConstructor
public class UserPublicKeyRepositoryImpl implements UserPublicKeyRepository {

    private final SpringDataMongoUserPublicKeyRepository mongoRepository;

    @Override
    public UserPublicKeyBundle save(UserPublicKeyBundle bundle) {
        UserPublicKeyDocument doc = mongoRepository.findByUserId(bundle.getUserId())
                .orElse(UserPublicKeyDocument.builder().userId(bundle.getUserId()).build());

        doc.setIdentityPublicKey(bundle.getIdentityPublicKey());
        doc.setSignedPreKey(bundle.getSignedPreKey());
        doc.setPreKeySignature(bundle.getPreKeySignature());
        doc.setKeyVersion(bundle.getKeyVersion() > 0 ? bundle.getKeyVersion() : doc.getKeyVersion() + 1);
        doc.setUpdatedAt(bundle.getUpdatedAt());

        UserPublicKeyDocument saved = mongoRepository.save(doc);
        return toDomain(saved);
    }

    @Override
    public Optional<UserPublicKeyBundle> findByUserId(String userId) {
        return mongoRepository.findByUserId(userId).map(this::toDomain);
    }

    private UserPublicKeyBundle toDomain(UserPublicKeyDocument doc) {
        return UserPublicKeyBundle.builder()
                .id(doc.getId())
                .userId(doc.getUserId())
                .identityPublicKey(doc.getIdentityPublicKey())
                .signedPreKey(doc.getSignedPreKey())
                .preKeySignature(doc.getPreKeySignature())
                .keyVersion(doc.getKeyVersion())
                .updatedAt(doc.getUpdatedAt())
                .build();
    }
}
