package com.mathvisionkids.api.studentprofile;

import com.mathvisionkids.api.auth.JwtUtil;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpStatus;
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
    private static final String PARENT_GRANT = "X-MathVision-Parent-Grant";
    private final ParentControlService controls;
    private final JwtUtil jwt;
    private final ParentPinRecoveryService recovery;

    ParentControlController(ParentControlService controls, JwtUtil jwt, ParentPinRecoveryService recovery) {
        this.controls = controls;
        this.jwt = jwt;
        this.recovery = recovery;
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
    ParentControlService.Settings unlock(Principal principal, @Valid @RequestBody Pin request,
            HttpServletRequest authRequest, HttpServletResponse response) {
        var unlocked = controls.unlock(principal.getName(), request.pin());
        var grant = jwt.issueParentSettingsGrant(principal.getName(), authRequest, unlocked.pinRevision());
        if (grant != null) response.setHeader(PARENT_GRANT, grant);
        return unlocked.settings();
    }

    @GetMapping("/settings")
    ParentControlService.Settings settings(Principal principal, HttpServletRequest request,
            @RequestHeader(name = PARENT_GRANT, required = false) String grant) {
        return controls.settings(principal.getName(), revision ->
                jwt.acceptsParentSettingsGrant(grant, principal.getName(), request, revision));
    }

    @PostMapping("/pin-code/request")
    ParentPinRecoveryService.Destination requestCode(Principal principal, @Valid @RequestBody CodeRequest request) {
        return recovery.request(principal.getName(), request.purpose());
    }

    @PostMapping("/pin-code/confirm")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    void confirmCode(Principal principal, @Valid @RequestBody CodeConfirmation request) {
        recovery.confirm(principal.getName(), request.purpose(), request.code(), request.pin());
    }

    @PutMapping("/daily-limit")
    ParentControlService.Settings save(Principal principal, @Valid @RequestBody DailyLimit request) {
        return controls.saveDailyLimit(principal.getName(), request.pin(), request.minutes());
    }

    @PutMapping("/game-limit")
    ParentControlService.Settings saveGameLimit(Principal principal, @Valid @RequestBody DailyLimit request) {
        return controls.saveGameLimit(principal.getName(), request.pin(), request.minutes());
    }

    record CodeRequest(@NotNull ParentPinRecoveryService.Purpose purpose) {}
    record CodeConfirmation(@NotNull ParentPinRecoveryService.Purpose purpose,
            @NotNull @Pattern(regexp = "[0-9]{6}") String code,
            @NotNull @Pattern(regexp = "[0-9]{6}") String pin) {}
    record Pin(@NotNull @Pattern(regexp = "[0-9]{6}") String pin) {}
    record DailyLimit(@NotNull @Pattern(regexp = "[0-9]{6}") String pin, @Min(1) @Max(1440) Integer minutes) {}
}
