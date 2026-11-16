package com.mathvisionkids.api.submission;

import java.security.Principal;
import java.util.List;
import java.util.UUID;
import org.springframework.http.CacheControl;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
class AssignedResultsController {
    private final AssignedResults results;

    AssignedResultsController(AssignedResults results) {
        this.results = results;
    }

    @GetMapping("/student/assignments/history")
    ResponseEntity<List<AssignedResults.HistoryItem>> history(Principal actor) {
        return ResponseEntity.ok().cacheControl(CacheControl.noStore()).body(results.history(actor.getName()));
    }

    @GetMapping("/teacher/assignments/action-center")
    ResponseEntity<AssignedResults.ActionCenter> actionCenter(Principal actor,
            @RequestParam(defaultValue = "ALL") AssignedResults.WorkFilter filter,
            @RequestParam(defaultValue = "0") int page) {
        return ResponseEntity.ok().cacheControl(CacheControl.noStore())
                .body(results.actionCenter(actor.getName(), filter, page));
    }

    @GetMapping("/teacher/assignments/{assignmentId}/results")
    ResponseEntity<AssignedResults.Publication> publication(Principal actor, @PathVariable UUID assignmentId) {
        return ResponseEntity.ok().cacheControl(CacheControl.noStore())
                .body(results.publication(actor.getName(), assignmentId));
    }
}
