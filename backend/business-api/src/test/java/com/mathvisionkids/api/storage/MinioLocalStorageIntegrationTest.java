package com.mathvisionkids.api.storage;

import io.minio.BucketExistsArgs;
import io.minio.ListObjectsArgs;
import io.minio.MinioClient;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.util.ReflectionTestUtils;
import static org.junit.jupiter.api.Assertions.*;

/** Opt-in, read-only check against the local MinIO; application data is never changed. */
@SpringBootTest
@ActiveProfiles("test")
@EnabledIfEnvironmentVariable(named="MATHVISION_MINIO_SMOKE", matches="true")
class MinioLocalStorageIntegrationTest {
    @Autowired ObjectStorageService storage;
    @Value("${minio.bucket-name}") String bucket;

    @Test void springStorageBeanAuthenticatesAndReadsTheExistingBucket() throws Exception {
        assertInstanceOf(MinioObjectStorageService.class, storage);
        var client=(MinioClient) ReflectionTestUtils.getField(storage,"minioClient");
        assertNotNull(client);
        assertTrue(client.bucketExists(BucketExistsArgs.builder().bucket(bucket).build()));
        for (var object : client.listObjects(ListObjectsArgs.builder().bucket(bucket).recursive(true).build())) {
            assertNotNull(object.get().objectName());
        }
    }
}
