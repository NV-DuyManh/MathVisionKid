package com.mathvisionkids.api.auth;

import com.google.api.client.googleapis.auth.oauth2.*;
import com.google.firebase.auth.*;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.*;
import org.junit.jupiter.api.*;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.util.ReflectionTestUtils;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class SocialAuthBoundaryTest {
    UserRepository users=mock(UserRepository.class);
    StudentRepository students=mock(StudentRepository.class);
    TeacherRepository teachers=mock(TeacherRepository.class);
    PasswordEncoder encoder=mock(PasswordEncoder.class);
    JwtUtil jwt=mock(JwtUtil.class);
    RefreshTokenService refresh=mock(RefreshTokenService.class);
    GoogleIdTokenVerifier verifier=mock(GoogleIdTokenVerifier.class);
    GoogleAuthService google=new GoogleAuthService(users,students,teachers,encoder,jwt,refresh,true,"configured-test-audience");
    GoogleLoginRequest googleRequest() {
        var request=new GoogleLoginRequest();request.setCredential("test-credential");request.setRole("TEACHER");return request;
    }
    void googlePayload(String email,boolean verified) throws Exception {
        var token=mock(GoogleIdToken.class);
        var payload=new GoogleIdToken.Payload().setEmail(email).setEmailVerified(verified).setSubject("verified-subject");
        when(token.getPayload()).thenReturn(payload);when(verifier.verify("test-credential")).thenReturn(token);
        ReflectionTestUtils.setField(google,"verifier",verifier);
    }
    @Test void unverifiedAndNonAuthoritativeEmailsCannotAutoLinkExistingAccounts() throws Exception {
        googlePayload("known@gmail.com",false);assertThrows(ApiException.class,()->google.login(googleRequest()));
        googlePayload("known@third-party.example",true);assertThrows(ApiException.class,()->google.login(googleRequest()));
        verifyNoInteractions(users,jwt,refresh);
    }
    @Test void invalidTokenCannotCreateASession() throws Exception {
        ReflectionTestUtils.setField(google,"verifier",verifier);
        assertThrows(ApiException.class,()->google.login(googleRequest()));verifyNoInteractions(users,jwt,refresh);
    }
    @Test void requestedTeacherRoleCannotPromoteAnExistingStudent() throws Exception {
        googlePayload("known@gmail.com",true);
        var pupil=new Student();pupil.setId(UUID.randomUUID());pupil.setEmail("known@gmail.com");pupil.setRole("STUDENT");pupil.setActive(true);
        when(users.findByGoogleSubject("verified-subject")).thenReturn(Optional.of(pupil));
        google.login(googleRequest());verify(jwt).generateToken("known@gmail.com","STUDENT");
    }
    @Test void disabledAccountCannotReceiveTokens() throws Exception {
        googlePayload("known@gmail.com",true);
        var pupil=new Student();pupil.setEmail("known@gmail.com");pupil.setRole("STUDENT");pupil.setActive(false);
        when(users.findByGoogleSubject("verified-subject")).thenReturn(Optional.of(pupil));
        assertThrows(ApiException.class,()->google.login(googleRequest()));verifyNoInteractions(jwt,refresh);
    }
    @Test void facebookRejectsOtherProvidersAndUnverifiedNewEmailsWithoutLinkingByEmail() throws Exception {
        var firebase=mock(FirebaseAuth.class);var token=mock(FirebaseToken.class);
        var service=new FacebookAuthService(users,students,teachers,encoder,jwt,refresh,true,"test-project");
        ReflectionTestUtils.setField(service,"firebaseAuth",firebase);
        var request=new FacebookLoginRequest();request.setCredential("test-credential");request.setRole("STUDENT");request.setGradeLevel(3);
        when(firebase.verifyIdToken("test-credential",true)).thenReturn(token);
        when(token.getClaims()).thenReturn(Map.of("firebase",Map.of("sign_in_provider","password")));
        assertThrows(ApiException.class,()->service.login(request));verifyNoInteractions(users);
        when(token.getClaims()).thenReturn(Map.of("firebase",Map.of("sign_in_provider","facebook.com")));
        when(token.getUid()).thenReturn("facebook-subject");when(token.getEmail()).thenReturn("known@example.test");
        assertThrows(ApiException.class,()->service.login(request));
        verify(users,never()).findByEmail(anyString());verifyNoInteractions(jwt,refresh);
        when(token.isEmailVerified()).thenReturn(true);when(users.findByEmail("known@example.test")).thenReturn(Optional.of(new User()));
        assertThrows(ApiException.class,()->service.login(request));verify(users,never()).save(any());
    }
}
