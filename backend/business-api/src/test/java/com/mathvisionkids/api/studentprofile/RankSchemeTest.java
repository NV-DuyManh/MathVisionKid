package com.mathvisionkids.api.studentprofile;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class RankSchemeTest {
    @Test void legacyKeepsPreviousRankSemanticsAtTopBoundary() {
        assertEquals("Đồng III", LegacyStudentRank.at(0, null).name());
        assertEquals("Chiến Tướng", LegacyStudentRank.at(162, 201L).name());
        assertEquals("Chiến Tướng", LegacyStudentRank.at(162, null).name());
        assertEquals("Thách Đấu", LegacyStudentRank.at(162, 200L).name());
        assertEquals(1, LegacyStudentRank.at(162, 200L).scheme());
        assertEquals("Đại Cao Thủ I", LegacyStudentRank.at(161, 200L).name());
        assertEquals("Thách Đấu", LegacyStudentRank.milestones().getLast().name());
        assertTrue(LegacyStudentRank.milestones().stream().allMatch(row -> row.scheme() == 1));
        assertEquals("Thách Đấu", StudentRank.at(162, 201L).name());
        assertEquals("Thách Đấu", StudentRank.at(162, null).name());
        assertEquals("Huyền Thoại", StudentRank.at(162, 200L).name());
        assertEquals(2, StudentRank.at(162, 200L).scheme());
        assertTrue(StudentRank.milestones().stream().allMatch(row -> row.scheme() == 2));
    }
}
