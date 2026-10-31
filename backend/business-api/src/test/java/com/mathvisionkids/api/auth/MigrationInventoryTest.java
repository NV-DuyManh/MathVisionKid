package com.mathvisionkids.api.auth;

import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.util.*;
import java.util.regex.Pattern;
import static org.junit.jupiter.api.Assertions.*;

class MigrationInventoryTest {
    @Test void everyFlywayVersionIsUniqueAcrossMergedFeatures() throws Exception {
        var versions=new HashMap<Integer,String>(); var pattern=Pattern.compile("V(\\d+)__.*\\.sql");
        try(var paths=Files.list(Path.of("src/main/resources/db/migration"))) {
            for(var path:paths.toList()) {
                var match=pattern.matcher(path.getFileName().toString());
                if(match.matches()) assertNull(versions.put(Integer.parseInt(match.group(1)),path.toString()),
                    ()->"Duplicate migration version: "+path);
            }
        }
        assertTrue(versions.containsKey(23)); assertTrue(versions.containsKey(26));
    }
}
