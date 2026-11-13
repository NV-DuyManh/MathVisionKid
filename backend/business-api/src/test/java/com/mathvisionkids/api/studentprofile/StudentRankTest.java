package com.mathvisionkids.api.studentprofile;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class StudentRankTest {
    @Test void everyDivisionUsesItsOwnStarThreshold() {
        String[] names = {"Đồng", "Bạc", "Vàng", "Bạch Kim", "Kim Cương", "Tinh Anh"};
        int[] divisions = {3, 3, 4, 5, 5, 5};
        int[] sizes = {3, 4, 4, 5, 5, 5};
        String[] roman = {"", "I", "II", "III", "IV", "V"};
        int total = 0;
        for (int tier = 0; tier < names.length; tier++) {
            for (int division = divisions[tier]; division >= 1; division--) {
                String label = names[tier] + " " + roman[division];
                assertEquals(new StudentRank.Rank(label, 0, 0, sizes[tier]), StudentRank.at(total, null));
                total += sizes[tier];
                assertEquals(new StudentRank.Rank(label, 0, sizes[tier] - 1, sizes[tier]), StudentRank.at(total - 1, null));
            }
        }
        assertEquals(112, total);
        assertEquals("Cao Thủ", StudentRank.at(total, null).name());
    }

    @Test void masterAndDynamicChallengerBoundaries() {
        int[] master = {0, 9, 10, 19, 20, 29, 30, 39, 40, 49, 50, 99, 100};
        String[] names = {"Cao Thủ", "Cao Thủ", "Đại Cao Thủ IV", "Đại Cao Thủ IV", "Đại Cao Thủ III", "Đại Cao Thủ III",
                "Đại Cao Thủ II", "Đại Cao Thủ II", "Đại Cao Thủ I", "Đại Cao Thủ I", "Chiến Tướng", "Chiến Tướng", "Chiến Thần"};
        for (int i = 0; i < master.length; i++) {
            var rank = StudentRank.at(112 + master[i], null);
            assertEquals(names[i], rank.name());
            assertEquals(master[i], rank.masterStars());
        }
        assertEquals("Đại Cao Thủ I", StudentRank.at(161, 1L).name());
        assertEquals("Thách Đấu", StudentRank.at(162, 200L).name());
        assertEquals("Chiến Tướng", StudentRank.at(162, 201L).name());
        assertEquals("Chiến Thần", StudentRank.at(212, null).name());
    }
}
