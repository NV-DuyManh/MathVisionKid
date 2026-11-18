package com.mathvisionkids.api.studentprofile;

import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.security.Principal;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/student/app-usage")
public class StudentUsageController {
    private final StudentUsageService usage;

    StudentUsageController(StudentUsageService usage) {
        this.usage = usage;
    }

    @ModelAttribute
    void noStore(HttpServletResponse response) {
        response.setHeader("Cache-Control", "no-store");
    }

    @PostMapping("/heartbeat")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    void heartbeat(Principal principal, @Valid @RequestBody Heartbeat heartbeat) {
        usage.observe(principal.getName(), heartbeat.connectionId(), heartbeat.active());
    }

    @GetMapping("/week")
    StudentUsageService.Week week(Principal principal) {
        return usage.week(principal.getName());
    }

    record Heartbeat(@NotNull UUID connectionId, @NotNull Boolean active) {}
}
