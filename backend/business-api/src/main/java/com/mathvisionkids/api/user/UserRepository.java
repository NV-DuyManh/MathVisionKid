package com.mathvisionkids.api.user;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import java.util.Optional;
import java.util.UUID;

public interface UserRepository extends JpaRepository<User, UUID>, JpaSpecificationExecutor<User> {
    Optional<User> findByEmail(String email);
    Optional<User> findByGoogleSubject(String googleSubject);
    Optional<User> findByFacebookSubject(String facebookSubject);
    boolean existsByEmail(String email);
    long countByRole(String role);
    long countByRoleAndActive(String role, Boolean active);
}
