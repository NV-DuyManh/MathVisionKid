package com.mathvisionkids.api.studentprofile;

import jakarta.validation.constraints.*;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

final class ProfileDtos {
    record Edit(@NotBlank @Size(max = 40) String displayName, @NotBlank @Size(max = 16) String avatar,
                @NotNull Boolean leaderboardVisible, @Size(max = 32) String selectedTitle, Boolean removePhoto) {
        Edit(String displayName, String avatar, Boolean leaderboardVisible, String selectedTitle) {
            this(displayName, avatar, leaderboardVisible, selectedTitle, false);
        }
    }
    record PasswordChange(@NotBlank @Size(max = 200) String currentPassword,
                          @NotBlank @Size(min = 8, max = 72) String newPassword) {}
    record Classroom(UUID id, String name) {}
    record Title(String id, String name, String rarity, String description, long progress, long goal, boolean unlocked) {}
    record Activity(String source, Instant completedAt, int stars) {}
    record Stats(long lessons, long quizzes, long games, long days, long week, long month, long today, long streak) {}
    record Profile(String displayName, Integer gradeLevel, Instant joinedAt, List<Classroom> classrooms, String avatar,
                   boolean leaderboardVisible, String publicAlias, String selectedTitle, long stars, StudentRank.Rank rank,
                   String highestRank, Long position, Stats stats, List<Title> titles, List<Activity> history,
                   String avatarPhoto, boolean passwordLoginAvailable) {}
    record Entry(long position, String alias, String avatar, long stars, StudentRank.Rank rank, boolean self) {}
    record Leaderboard(List<Entry> entries, Long ownPosition) {}
    record GameAnswer(@NotNull @Min(0) @Max(4) Integer question, @NotNull @Min(-10000) @Max(10000) Integer answer) {}
    enum GameMode { ARITHMETIC_QUEST, RACE_TO_FINISH, TERRAIN_RACING, ENERGY_DEFENSE, PLANET_RESCUE, BLOCK_ISLAND }
    enum GameRewardStatus { AWARDED, REPEAT, DAILY_LIMIT, GAME_LIMIT, UNAVAILABLE }
    record Game(UUID id, int question, String prompt, int correct, int length, boolean completed, int stars,
                GameRewardStatus rewardStatus) {}

    private ProfileDtos() {}
}
