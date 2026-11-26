package com.mathvisionkids.api.auth;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withStatus;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class GoogleProfileClientTest {
    private static final String USER_INFO = "https://openidconnect.googleapis.com/v1/userinfo";
    private static final String PICTURE = "https://lh3.googleusercontent.com/a/synthetic-avatar";
    private GoogleProfileClient client;
    private MockRestServiceServer google;

    @BeforeEach
    void setUp() {
        var builder = RestClient.builder();
        client = new GoogleProfileClient(builder);
        google = MockRestServiceServer.bindTo(builder).build();
        ReflectionTestUtils.setField(client, "client", builder.build());
    }

    @Test
    void returnsPictureOnlyForTheVerifiedGoogleSubject() {
        google.expect(requestTo(USER_INFO)).andExpect(header(HttpHeaders.AUTHORIZATION, "Bearer synthetic-token"))
                .andRespond(withSuccess("""
                        {"sub":"other","picture":"%s"}
                        """.formatted(PICTURE), MediaType.APPLICATION_JSON));
        google.expect(requestTo(USER_INFO)).andRespond(withSuccess("""
                {"sub":"student","picture":"%s"}
                """.formatted(PICTURE), MediaType.APPLICATION_JSON));

        assertNull(client.avatar("synthetic-token", "student"));
        assertEquals(PICTURE, client.avatar("synthetic-token", "student"));
        google.verify();
    }

    @Test
    void unavailableProfileDoesNotBreakLogin() {
        google.expect(requestTo(USER_INFO)).andRespond(withStatus(HttpStatus.SERVICE_UNAVAILABLE));
        assertNull(client.avatar(null, "student"));
        assertNull(client.avatar("synthetic-token", "student"));
        google.verify();
    }
}
