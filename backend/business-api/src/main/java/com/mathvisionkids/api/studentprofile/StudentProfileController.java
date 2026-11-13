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
    private final StudentAccountService account;

    public StudentProfileController(StudentProfileService profiles, StudentGameService games, StudentAccountService account) {
        this.profiles = profiles;
        this.games = games;
        this.account = account;
    }

    @ModelAttribute
    void noStore(HttpServletResponse response) {
        response.setHeader("Cache-Control", "no-store");
    }

    @GetMapping("/profile")
    public Profile profile(Principal principal) { return profiles.get(principal.getName()); }

    @PutMapping("/profile")
    public Profile update(Principal principal, @Valid @RequestBody Edit edit) { return profiles.update(principal.getName(), edit); }

    @PutMapping(value = "/profile/photo", consumes = "multipart/form-data")
    public Profile photo(Principal principal, @RequestParam("file") org.springframework.web.multipart.MultipartFile file) {
        return account.photo(principal.getName(), file);
    }

    @PostMapping("/profile/password")
    public com.mathvisionkids.api.auth.AuthResponse password(Principal principal, @Valid @RequestBody PasswordChange request) {
        return account.password(principal.getName(), request);
    }

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
