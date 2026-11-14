package com.mathvisionkids.api.studentprofile;

import java.util.List;
import java.util.ArrayList;

public final class StudentRank {
    private record Tier(String name, int divisions, int stars) {}
    private static final List<Tier> TIERS = List.of(new Tier("Đồng", 3, 3), new Tier("Bạc", 3, 4),
            new Tier("Vàng", 4, 4), new Tier("Bạch Kim", 5, 5), new Tier("Kim Cương", 5, 5), new Tier("Tinh Anh", 5, 5));
    private static final List<String> ROMAN = List.of("", "I", "II", "III", "IV", "V");
    private static final long MASTER = TIERS.stream().mapToLong(t -> t.divisions * t.stars).sum();
    public static final int CHALLENGER_SIZE = 200;
    public static final long CHALLENGER_MIN_STARS = MASTER + 50;

    public record Rank(String name, long masterStars, long progress, long goal) {}
    public record Milestone(String name, long stars, Integer top) {}

    public static List<Milestone> milestones() {
        List<Milestone> result = new ArrayList<>();
        long stars = 0;
        for (Tier tier : TIERS) {
            result.add(new Milestone(tier.name(), stars, null));
            stars += (long) tier.divisions() * tier.stars();
        }
        result.add(new Milestone(at(stars, null).name(), stars, null));
        result.add(new Milestone("Đại Cao Thủ", MASTER + 10, null));
        result.add(new Milestone(at(MASTER + 50, null).name(), MASTER + 50, null));
        result.add(new Milestone(at(MASTER + 100, null).name(), MASTER + 100, null));
        result.add(new Milestone(at(CHALLENGER_MIN_STARS, (long) CHALLENGER_SIZE).name(), CHALLENGER_MIN_STARS, CHALLENGER_SIZE));
        return List.copyOf(result);
    }

    private StudentRank() {}

    public static Rank at(long total, Long position) {
        if (total < 0) throw new IllegalArgumentException("Stars must be nonnegative");
        if (position != null && position >= 1 && position <= CHALLENGER_SIZE && total >= CHALLENGER_MIN_STARS)
            return new Rank("Thách Đấu", total - MASTER, 0, 0);
        long remaining = total;
        for (Tier tier : TIERS) {
            long span = (long) tier.divisions * tier.stars;
            if (remaining < span) return new Rank(tier.name + " " + ROMAN.get(tier.divisions - (int) (remaining / tier.stars)),
                    0, remaining % tier.stars, tier.stars);
            remaining -= span;
        }
        if (remaining < 10) return new Rank("Cao Thủ", remaining, remaining, 10);
        if (remaining < 50) return new Rank("Đại Cao Thủ " + ROMAN.get(5 - (int) remaining / 10), remaining, remaining % 10, 10);
        if (remaining < 100) return new Rank("Chiến Tướng", remaining, remaining - 50, 50);
        return new Rank("Chiến Thần", remaining, 0, 0);
    }
}
