# MathVision Kids - Phase 3.1 Business API Completion

## 1. Goal and Overview
The MathVision Kids Phase 3.1 task involved finalizing the Spring Boot Business API. The key objectives were to ensure robust transaction management, eliminate orphaned entities (specifically files/images not deleted when a transaction rolls back or fails), secure API endpoints using RBAC, expose OpenAPI (Swagger) documentation, and fix test suite instabilities. A strict requirement was to build an environment that guarantees 100% stable integration tests against a real PostgreSQL database with Testcontainers, ensuring no leaked state between test cases.

## 2. Changes Made
- **File Upload Transactional Integrity:** Fixed the `@Transactional` wrapper around image uploading and batch creation in `TeacherBatchController` and `BatchService`. MinIO upload logic is executed only after the transaction is fully committed to prevent orphaned files in MinIO during DB rollback.
- **Test Transaction Rollback:** Refactored `SpringBootTest` annotations. We transitioned from `RANDOM_PORT` with real HTTP calls to `@AutoConfigureMockMvc` for test controllers that required transactional boundaries. This correctly binds tests to the `@Transactional` boundary and rolls back database commits effectively between tests.
- **Batch Image Validation:** Increased the minimum file upload limit in `BatchService` from 1 image to 10 images as per validation logic.
- **Exception Handling & ApiException:** Updated the `TeacherBatchController` to properly rethrow `ApiException` (which returns a custom `ApiErrorResponse`) instead of wrapping it in `RuntimeException` which results in a default 500 error.
- **Static Assets and OpenAPI:** Fixed `SecurityConfig` to properly permit `/api-docs/**` and `/swagger-ui/**`, allowing the Springdoc OpenAPI parser to serve API specs without authentication. Changed the hardcoded `/v3/api-docs` path to `/api-docs` in `application.yml` and explicitly allowed it.
- **Classroom Seed Data:** Cleaned up `SeedDataInitializer` logic which inserted data causing duplicate key constraint violations in `@Transactional` tests that persisted changes before tests wiped tables. Moved test setup to use `jdbcTemplate` cleanup for robustness.

## 3. Testing and Validation
- **Integration Tests:** The entire test suite (`./gradlew test`) executes reliably without state bleed between tests. All 26 tests across controllers (`TeacherBatchControllerTest`, `StudentSubmissionControllerTest`, `AuthControllerTest`, etc.) and services pass successfully.
- **Testcontainers & Flyway:** The setup spins up isolated PostgreSQL and MinIO environments. Database migrations (Flyway) automatically validate and execute schema baseline.
- **Runtime API Verification:** Executed `docker-compose up -d` against the full system. Both `/actuator/health` and `/api-docs` (Swagger UI) respond correctly without errors (200 OK) demonstrating a ready business layer.

## 4. Current Status
**Phase 3.1 Business API Completion: FULLY IMPLEMENTED AND VERIFIED.**
The backend is now ready for the AI boundary integration in Phase 4.
