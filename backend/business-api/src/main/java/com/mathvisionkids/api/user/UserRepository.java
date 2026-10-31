package com.mathvisionkids.api.user;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import java.util.Optional;
import java.util.UUID;

public interface UserRepository extends JpaRepository<User, UUID>, JpaSpecificationExecutor<User> {
    // Lock only the root row: JOINED inheritance can add nullable outer joins,
    // which PostgreSQL cannot lock with an unqualified FOR UPDATE.
    @org.springframework.data.jpa.repository.Query(value="select 1 from users where email = :email for update", nativeQuery=true)
    Optional<Integer> lockPasswordResetUser(@org.springframework.data.repository.query.Param("email") String email);
    Optional<User> findByEmail(String email);
    Optional<User> findByGoogleSubject(String googleSubject);
    Optional<User> findByFacebookSubject(String facebookSubject);
    boolean existsByEmail(String email);
    long countByRole(String role);
    long countByRoleAndActive(String role, Boolean active);
}
