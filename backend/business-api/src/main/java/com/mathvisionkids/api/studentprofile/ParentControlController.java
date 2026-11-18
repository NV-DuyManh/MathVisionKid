package com.mathvisionkids.api.studentprofile;

import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import org.springframework.web.bind.annotation.*;

import java.security.Principal;

@RestController
@RequestMapping("/api/v1/student/parent-control")
public class ParentControlController {
    private final ParentControlService controls;

    ParentControlController(ParentControlService controls) {
        this.controls = controls;
    }

    @ModelAttribute
    void noStore(HttpServletResponse response) {
        response.setHeader("Cache-Control", "no-store");
    }

    @GetMapping("/status")
    ParentControlService.Status status(Principal principal) {
        return controls.status(principal.getName());
    }

    @PostMapping("/pin")
    ParentControlService.Settings setup(Principal principal, @Valid @RequestBody Pin request) {
        return controls.setup(principal.getName(), request.pin());
    }

    @PostMapping("/unlock")
    ParentControlService.Settings unlock(Principal principal, @Valid @RequestBody Pin request) {
        return controls.unlock(principal.getName(), request.pin());
    }

    @PutMapping("/daily-limit")
    ParentControlService.Settings save(Principal principal, @Valid @RequestBody DailyLimit request) {
        return controls.saveDailyLimit(principal.getName(), request.pin(), request.minutes());
    }

    record Pin(@NotNull @Pattern(regexp = "[0-9]{6}") String pin) {}
    record DailyLimit(@NotNull @Pattern(regexp = "[0-9]{6}") String pin, @Min(1) @Max(1440) Integer minutes) {}
}
