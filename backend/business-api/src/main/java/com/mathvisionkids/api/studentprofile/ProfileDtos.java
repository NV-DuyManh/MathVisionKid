package com.mathvisionkids.api.studentprofile;

import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.*;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

final class ProfileDtos {
    record Edit(String displayName, @Size(max = 16) String avatar,
                Boolean leaderboardVisible, @Size(max = 32) String selectedTitle, Boolean removePhoto,
                Boolean leaderboardNameHidden, Boolean leaderboardPhotoVisible, UUID privacyRevision) {
        Edit(String displayName, String avatar, Boolean leaderboardVisible, String selectedTitle,
             Boolean removePhoto, Boolean leaderboardNameHidden, Boolean leaderboardPhotoVisible) {
            this(displayName, avatar, leaderboardVisible, selectedTitle, removePhoto, leaderboardNameHidden, leaderboardPhotoVisible, null);
        }
        Edit(String displayName, String avatar, Boolean leaderboardVisible, String selectedTitle) {
            this(displayName, avatar, leaderboardVisible, selectedTitle, false, null, null);
        }
        Edit(String displayName, String avatar, Boolean leaderboardVisible, String selectedTitle, Boolean removePhoto) {
            this(displayName, avatar, leaderboardVisible, selectedTitle, removePhoto, null, null);
        }
        Edit(String displayName, String avatar, Boolean leaderboardVisible, String selectedTitle,
             Boolean removePhoto, Boolean leaderboardNameHidden) {
            this(displayName, avatar, leaderboardVisible, selectedTitle, removePhoto, leaderboardNameHidden, null);
        }
    }
    record PasswordChange(@NotBlank @Size(max = 200) String currentPassword,
                          @NotBlank @Size(min = 8, max = 72) String newPassword) {}
    record Classroom(UUID id, String name) {}
    record Title(String id, String name, String rarity, String description, long progress, long goal, boolean unlocked) {}
    record Activity(String source, Instant completedAt, int stars) {}
    record ActivityPage(List<Activity> entries, long page, long totalPages) {}
    record Stats(long lessons, long quizzes, long games, long days, long week, long month, long today, long streak) {}
    record Profile(String displayName, Integer gradeLevel, Instant joinedAt, List<Classroom> classrooms, String avatar,
                   boolean leaderboardVisible, String publicAlias, String selectedTitle, long stars, StudentRank.Rank rank,
                   String highestRank, Long position, Stats stats, List<Title> titles, List<Activity> history,
                   String avatarPhoto, boolean passwordLoginAvailable, boolean leaderboardNameHidden, boolean googleLinked,
                   boolean leaderboardPhotoVisible, UUID privacyRevision) {}
    record Entry(long position, String alias, String avatar, long stars, StudentRank.Rank rank, boolean self,
                 @JsonInclude(JsonInclude.Include.NON_NULL) String avatarPhoto) {}
    record Leaderboard(List<Entry> entries, Long ownPosition, Integer gradeLevel) {}
    record GameAnswer(@NotNull @Min(0) @Max(4) Integer question, @NotNull @Min(-10000) @Max(10000) Integer answer) {}
    enum GameMode { ARITHMETIC_QUEST, RACE_TO_FINISH, TERRAIN_RACING, ENERGY_DEFENSE, PLANET_RESCUE, BLOCK_ISLAND }
    enum GameRewardStatus { AWARDED, REPEAT, DAILY_LIMIT, GAME_LIMIT, UNAVAILABLE }
    record Game(UUID id, int question, String prompt, int correct, int length, boolean completed, int stars,
                GameRewardStatus rewardStatus) {}

    private ProfileDtos() {}
}
