package com.mathvisionkids.api.quiz;

import jakarta.persistence.LockModeType;
import org.springframework.data.domain.*;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.repository.query.Param;
import java.util.*;

interface QuizRepository extends JpaRepository<Quiz, UUID> {
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select q from Quiz q where q.id=:id and q.studentId=:student")
    Optional<Quiz> ownedForUpdate(@Param("id") UUID id, @Param("student") UUID student);
    Optional<Quiz> findByIdAndStudentId(UUID id, UUID student);
    Optional<Quiz> findFirstByStudentIdAndSourceFingerprintOrderByCreatedAtAsc(UUID student, String fingerprint);
    Optional<Quiz> findByStudentIdAndSourceTypeAndSourceFingerprint(UUID student, String type, String fingerprint);
    Page<Quiz> findByStudentId(UUID student, Pageable pageable);
    Page<Quiz> findByStudentIdAndStatusIn(UUID student, Collection<String> statuses, Pageable pageable);
    @Query("select count(q) from Quiz q where q.studentId=:student and q.status in :statuses and q.firstCompletedAt is null")
    long countByStudentIdAndStatusIn(@Param("student") UUID student, @Param("statuses") Collection<String> statuses);
    @Query("select q from Quiz q where q.studentId=:student and q.status in :statuses and q.firstCompletedAt is null")
    Page<Quiz> findPendingLibrary(@Param("student") UUID student, @Param("statuses") Collection<String> statuses, Pageable pageable);
    @Query("select q from Quiz q where q.studentId=:student and (q.status='COMPLETED' or q.firstCompletedAt is not null)")
    Page<Quiz> findCompletedLibrary(@Param("student") UUID student, Pageable pageable);
    @Modifying
    @Query("update Quiz q set q.status='INVALIDATED' where q.studentId=:student and q.status<>'COMPLETED' and q.firstCompletedAt is null and q.sourceId in (select s.sourceId from QuizSource s where s.studentId=:student and s.preparationId=:preparation and s.sourceType=q.sourceType)")
    int invalidatePreparation(@Param("student") UUID student,@Param("preparation") UUID preparation);
    @Query("select coalesce(sum(q.stars),0) from Quiz q where q.studentId=:student and q.status<>'INVALIDATED'")
    long totalStars(@Param("student") UUID student);
}

interface QuizSourceRepository extends JpaRepository<QuizSource, UUID> {
    Optional<QuizSource> findByStudentIdAndSourceTypeAndSourceId(UUID student, String type, String source);
}

interface QuizPreparationRepository extends JpaRepository<QuizPreparation, UUID> {
    List<QuizPreparation> findTop100ByStatusOrderByUpdatedAtAsc(String status);
    Optional<QuizPreparation> findByStudentIdAndWorkflowKey(UUID student, UUID workflow);
    Optional<QuizPreparation> findByIdAndStudentId(UUID id, UUID student);
    Optional<QuizPreparation> findFirstByStudentIdAndFingerprintOrderByUpdatedAtDesc(UUID student, String fingerprint);
}

interface QuizAttemptRepository extends JpaRepository<QuizAttempt, UUID> {
    Optional<QuizAttempt> findByQuizIdAndRequestId(UUID quiz, UUID request);
    List<QuizAttempt> findByQuizIdOrderByAttemptNumber(UUID quiz);
    long countByQuizId(UUID quiz);
}
