package com.mathvisionkids.api.studentprofile;

import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.security.Principal;
import java.util.UUID;
import static com.mathvisionkids.api.studentprofile.ProfileDtos.*;

@RestController
@RequestMapping("/api/v1/student")
public class StudentProfileController {
    private final StudentProfileService profiles;
    private final StudentGameService games;

    public StudentProfileController(StudentProfileService profiles, StudentGameService games) {
        this.profiles = profiles;
        this.games = games;
    }

    @ModelAttribute
    void noStore(HttpServletResponse response) {
        response.setHeader("Cache-Control", "no-store");
    }

    @GetMapping("/profile")
    public Profile profile(Principal principal) { return profiles.get(principal.getName()); }

    @PutMapping("/profile")
    public Profile update(Principal principal, @Valid @RequestBody Edit edit) { return profiles.update(principal.getName(), edit); }

    @GetMapping("/leaderboard")
    public Leaderboard leaderboard(Principal principal, @RequestParam(required = false) UUID classroom) {
        return profiles.leaderboard(principal.getName(), classroom);
    }

    @PostMapping("/game-runs")
    public Game start(Principal principal) { return games.start(principal.getName()); }

    @PostMapping("/game-runs/{id}/answers")
    public Game answer(Principal principal, @PathVariable UUID id, @Valid @RequestBody GameAnswer answer) {
        return games.answer(principal.getName(), id, answer);
    }
}
