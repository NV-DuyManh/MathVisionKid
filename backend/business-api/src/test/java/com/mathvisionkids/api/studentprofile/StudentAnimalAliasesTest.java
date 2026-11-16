package com.mathvisionkids.api.studentprofile;

import java.util.HashSet;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class StudentAnimalAliasesTest {
    @Test void usesEachAnimalBeforeAddingNumericSuffixes() {
        assertTrue(StudentAnimalAliases.ANIMALS.size() > 50);
        var used = new HashSet<String>();
        for (int i = 0; i < StudentAnimalAliases.ANIMALS.size(); i++) {
            String alias = StudentAnimalAliases.next(used);
            assertTrue(StudentAnimalAliases.ANIMALS.contains(alias));
            assertTrue(used.add(alias));
            assertTrue(alias.length() <= 32);
        }
        String next = StudentAnimalAliases.next(used);
        assertTrue(next.endsWith(" 2"));
        assertTrue(used.add(next));
        assertFalse(used.contains(StudentAnimalAliases.next(used)));
    }
}
