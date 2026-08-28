package org.example.chat.presentation.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.example.chat.domain.model.UserProfile;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserProfileDto {
    private String id;
    private String email;
    private String displayName;
    private String avatarUrl;
    private boolean isOnline;

    public static UserProfileDto fromDomain(UserProfile user) {
        return UserProfileDto.builder()
                .id(user.getId())
                .email(user.getEmail())
                .displayName(user.getDisplayName())
                .avatarUrl(user.getAvatarUrl())
                .isOnline(user.isOnline())
                .build();
    }
}
