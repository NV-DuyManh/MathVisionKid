package com.mathvisionkids.api.classroom;

import com.mathvisionkids.api.common.ApiException;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
class ClassroomJoinLimit {
    private final JdbcTemplate jdbc;

    ClassroomJoinLimit(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public void check(UUID studentId, boolean numericCode) {
        int updated = jdbc.update("""
                insert into classroom_join_limits (student_id, window_start, attempts)
                values (?, floor(extract(epoch from clock_timestamp()) / 60)::bigint, 1)
                on conflict (student_id) do update set
                    window_start = greatest(classroom_join_limits.window_start, excluded.window_start),
                    attempts = case when classroom_join_limits.window_start < excluded.window_start
                        then 1 else classroom_join_limits.attempts + 1 end
                where classroom_join_limits.window_start < excluded.window_start
                    or classroom_join_limits.attempts < 20
                """, studentId);
        if (updated == 0 || (numericCode && !takeCodeAttempt())) {
            throw new ApiException("JOIN_LIMIT", "Em chờ một chút rồi thử lại nhé.", HttpStatus.TOO_MANY_REQUESTS);
        }
    }

    private boolean takeCodeAttempt() {
        return jdbc.update("""
                insert into classroom_code_limit (id, window_start, attempts)
                values (1, floor(extract(epoch from clock_timestamp()) / 60)::bigint, 1)
                on conflict (id) do update set
                    window_start = greatest(classroom_code_limit.window_start, excluded.window_start),
                    attempts = case when classroom_code_limit.window_start < excluded.window_start
                        then 1 else classroom_code_limit.attempts + 1 end
                where classroom_code_limit.window_start < excluded.window_start
                    or classroom_code_limit.attempts < 300
                """) == 1;
    }
}
