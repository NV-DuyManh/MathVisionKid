package com.mathvisionkids.api.studentprofile;

import static com.mathvisionkids.api.studentprofile.ProfileDtos.*;

final class RankScheme {
    private RankScheme() {}

    static boolean modern(String client) { return "student-rank-v2".equals(client); }

    private static StudentRank.Rank legacy(long stars, StudentRank.Rank rank) {
        // The two schemes have the same 162-star global Top 200 eligibility.
        return LegacyStudentRank.at(stars, "Huyền Thoại".equals(rank.name()) ? 200L : null);
    }

    static Profile profile(Profile p, String client) {
        if (modern(client)) return p;
        var rank = legacy(p.stars(), p.rank());
        return new Profile(p.displayName(), p.gradeLevel(), p.joinedAt(), p.classrooms(), p.avatar(),
                p.leaderboardVisible(), p.publicAlias(), p.selectedTitle(), p.stars(), rank,
                "Huyền Thoại".equals(p.highestRank()) ? "Thách Đấu" : rank.name(), p.position(), p.stats(),
                p.titles(), p.history(), p.avatarPhoto(), p.passwordLoginAvailable(), p.leaderboardNameHidden(), p.googleLinked(), p.leaderboardPhotoVisible());
    }

    static Leaderboard board(Leaderboard board, String client) {
        if (modern(client)) return board;
        return new Leaderboard(board.entries().stream().map(e -> new Entry(e.position(), e.alias(), e.avatar(),
                e.stars(), legacy(e.stars(), e.rank()), e.self(), e.avatarPhoto())).toList(), board.ownPosition(), board.gradeLevel());
    }
}
