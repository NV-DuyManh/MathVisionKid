package com.mathvisionkids.api.studentprofile;

import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.security.Principal;
import java.util.List;
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
    public Profile profile(Principal principal, @RequestHeader(value = "X-MathVision-Client", required = false) String client) { return RankScheme.profile(profiles.get(principal.getName()), client); }

    @PutMapping("/profile")
    public Profile update(Principal principal, @Valid @RequestBody Edit edit, @RequestHeader(value = "X-MathVision-Client", required = false) String client) { return RankScheme.profile(profiles.update(principal.getName(), edit), client); }

    @PutMapping(value = "/profile/photo", consumes = "multipart/form-data")
    public Profile photo(Principal principal, @RequestParam("file") org.springframework.web.multipart.MultipartFile file,
                         @RequestHeader(value = "X-MathVision-Client", required = false) String client) {
        return RankScheme.profile(account.photo(principal.getName(), file), client);
    }

    @PostMapping("/profile/password")
    public com.mathvisionkids.api.auth.AuthResponse password(Principal principal, @Valid @RequestBody PasswordChange request) {
        return account.password(principal.getName(), request);
    }

    @GetMapping("/star-history")
    public ActivityPage starHistory(Principal principal, @RequestParam(defaultValue = "1") long page) {
        return profiles.starHistory(principal.getName(), page);
    }

    @GetMapping("/leaderboard")
    public Leaderboard leaderboard(Principal principal, @RequestParam(required = false) UUID classroom,
                                   @RequestParam(defaultValue = "false") boolean allGrades,
                                   @RequestHeader(value = "X-MathVision-Client", required = false) String client) {
        return RankScheme.board(profiles.leaderboard(principal.getName(), classroom, allGrades), client);
    }

    @GetMapping("/rank-milestones")
    public List<StudentRank.Milestone> rankMilestones(@RequestHeader(value = "X-MathVision-Client", required = false) String client) {
        return RankScheme.modern(client) ? StudentRank.milestones() : LegacyStudentRank.milestones();
    }

    @PostMapping("/game-runs")
    public Game start(Principal principal, @RequestParam(defaultValue = "ARITHMETIC_QUEST") GameMode mode) {
        return games.start(principal.getName(), mode);
    }

    @GetMapping("/game-runs/{id}")
    public Game game(Principal principal, @PathVariable UUID id) { return games.get(principal.getName(), id); }

    @PostMapping("/game-runs/{id}/answers")
    public Game answer(Principal principal, @PathVariable UUID id, @Valid @RequestBody GameAnswer answer) {
        return games.answer(principal.getName(), id, answer);
    }
}
