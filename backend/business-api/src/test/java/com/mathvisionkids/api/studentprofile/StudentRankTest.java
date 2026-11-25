package com.mathvisionkids.api.studentprofile;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class StudentRankTest {
    private static final String[] NAMES = {
            "Sắt III", "Sắt II", "Sắt I", "Đồng III", "Đồng II", "Đồng I",
            "Bạc III", "Bạc II", "Bạc I", "Vàng III", "Vàng II", "Vàng I",
            "Bạch Kim V", "Bạch Kim IV", "Bạch Kim III", "Bạch Kim II", "Bạch Kim I",
            "Kim Cương V", "Kim Cương IV", "Kim Cương III", "Kim Cương II", "Kim Cương I",
            "Cao Thủ", "Đại Cao Thủ", "Thách Đấu", "Huyền Thoại"
    };
    private static final long[] STARS = {0,3,6,9,12,15,18,21,24,27,30,33,37,42,47,52,57,62,67,72,77,82,87,122,162,162};

    @Test void allTwentySixMilestonesMatchExpectedOrderAndCosts() {
        var rows = StudentRank.milestones();
        assertEquals(26, rows.size());
        for (int i = 0; i < rows.size(); i++) {
            var row = rows.get(i);
            assertEquals(NAMES[i], row.name());
            assertEquals(STARS[i], row.stars());
            if (i < 25) assertNull(row.top()); else assertEquals(200, row.top());
            assertEquals(NAMES[i], StudentRank.at(row.stars(), row.top() == null ? null : row.top().longValue()).name());
        }
    }

    @Test void everyStarBeforeTopRankHasCorrectDivisionAndProgress() {
        for (int i = 0; i < 24; i++) {
            long cost = STARS[i+1]-STARS[i];
            for (long total = STARS[i]; total < STARS[i+1]; total++) {
                var expected = new StudentRank.Rank(NAMES[i], Math.max(0,total-87),total-STARS[i],cost);
                assertEquals(expected,StudentRank.at(total,null),"stars="+total);
                assertEquals(expected,StudentRank.at(total,1L),"top cannot skip threshold");
            }
        }
    }

    @Test void highRanksKeepThresholdAndTop200Qualification() {
        assertEquals(new StudentRank.Rank("Cao Thủ",0,0,35),StudentRank.at(87,null));
        assertEquals(new StudentRank.Rank("Cao Thủ",34,34,35),StudentRank.at(121,null));
        assertEquals(new StudentRank.Rank("Đại Cao Thủ",35,0,40),StudentRank.at(122,null));
        assertEquals(new StudentRank.Rank("Đại Cao Thủ",74,39,40),StudentRank.at(161,1L));
        assertEquals("Huyền Thoại",StudentRank.at(162,200L).name());
        assertEquals("Thách Đấu",StudentRank.at(162,201L).name());
        assertEquals("Thách Đấu",StudentRank.at(212,null).name());
        assertEquals("Huyền Thoại",StudentRank.at(212,1L).name());
        assertEquals("Thách Đấu",StudentRank.at(162,0L).name());
        assertEquals("Thách Đấu",StudentRank.at(162,-1L).name());
        assertThrows(IllegalArgumentException.class,()->StudentRank.at(-1,null));
        assertEquals("Thách Đấu",StudentRank.at(Long.MAX_VALUE,null).name());
    }
}
