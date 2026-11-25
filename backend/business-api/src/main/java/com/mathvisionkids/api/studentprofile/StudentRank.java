package com.mathvisionkids.api.studentprofile;

import java.util.List;
import java.util.ArrayList;

public final class StudentRank {
    private record Tier(String name, List<Integer> costs) {}
    private static final List<Tier> TIERS = List.of(
            new Tier("Sắt", List.of(3, 3, 3)),
            new Tier("Đồng", List.of(3, 3, 3)),
            new Tier("Bạc", List.of(3, 3, 3)),
            new Tier("Vàng", List.of(3, 3, 4)),
            new Tier("Bạch Kim", List.of(5, 5, 5, 5, 5)),
            new Tier("Kim Cương", List.of(5, 5, 5, 5, 5)));
    private static final List<String> ROMAN = List.of("", "I", "II", "III", "IV", "V");
    // Keep the entry thresholds for the approved rank progression.
    private static final long MASTER = TIERS.stream().flatMap(tier -> tier.costs().stream())
            .mapToLong(Integer::longValue).sum();
    private static final long GRANDMASTER_ENTRY = 122;
    public static final int CHALLENGER_SIZE = 200;
    public static final long CHALLENGER_MIN_STARS = 162;

    public record Rank(String name, long masterStars, long progress, long goal) {}
    public record Milestone(String name, long stars, Integer top) {}

    private static final List<Milestone> MILESTONES = buildMilestones();

    private StudentRank() {}

    private static List<Milestone> buildMilestones() {
        List<Milestone> result = new ArrayList<>();
        long stars = 0;
        for (Tier tier : TIERS) {
            for (int i = 0; i < tier.costs().size(); i++) {
                result.add(new Milestone(tier.name() + " " + ROMAN.get(tier.costs().size() - i), stars, null));
                stars += tier.costs().get(i);
            }
        }
        result.add(new Milestone("Cao Thủ", stars, null));
        result.add(new Milestone("Đại Cao Thủ", GRANDMASTER_ENTRY, null));
        result.add(new Milestone("Thách Đấu", CHALLENGER_MIN_STARS, null));
        result.add(new Milestone("Huyền Thoại", CHALLENGER_MIN_STARS, CHALLENGER_SIZE));
        return List.copyOf(result);
    }

    public static List<Milestone> milestones() { return MILESTONES; }

    public static Rank at(long total, Long position) {
        if (total < 0) throw new IllegalArgumentException("Stars must be nonnegative");
        long masterStars = Math.max(0, total - MASTER);
        if (total >= CHALLENGER_MIN_STARS && position != null && position >= 1 && position <= CHALLENGER_SIZE)
            return new Rank("Huyền Thoại", masterStars, 0, 0);
        for (int i = MILESTONES.size() - 2; i >= 0; i--) {
            Milestone row = MILESTONES.get(i);
            if (total < row.stars()) continue;
            long goal = MILESTONES.get(i + 1).stars() - row.stars();
            return new Rank(row.name(), masterStars, goal == 0 ? 0 : total - row.stars(), goal);
        }
        throw new IllegalStateException("Missing starting rank");
    }
}
