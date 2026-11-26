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
    RefreshTokenService refresh=mock(RefreshTokenService.class);
    GoogleIdTokenVerifier verifier=mock(GoogleIdTokenVerifier.class);
    com.mathvisionkids.api.studentprofile.StudentProfileService profiles=mock(com.mathvisionkids.api.studentprofile.StudentProfileService.class);
    GoogleProfileClient googleProfiles = mock(GoogleProfileClient.class);
    GoogleAuthService google=new GoogleAuthService(users,students,teachers,encoder,refresh,profiles,googleProfiles,true,"configured-test-audience");
    GoogleLoginRequest googleRequest() {
        var request=new GoogleLoginRequest();request.setCredential("test-credential");request.setRole("TEACHER");return request;
    }
    GoogleIdToken.Payload googlePayload(String email,boolean verified) throws Exception {
        var token=mock(GoogleIdToken.class);
        var payload=new GoogleIdToken.Payload().setEmail(email).setEmailVerified(verified).setSubject("verified-subject");
        when(token.getPayload()).thenReturn(payload);when(verifier.verify("test-credential")).thenReturn(token);
        ReflectionTestUtils.setField(google,"verifier",verifier);
        return payload;
    }
    @Test void unverifiedAndNonAuthoritativeEmailsCannotAutoLinkExistingAccounts() throws Exception {
        googlePayload("known@gmail.com",false);assertThrows(ApiException.class,()->google.login(googleRequest()));
        googlePayload("known@third-party.example",true);assertThrows(ApiException.class,()->google.login(googleRequest()));
        verifyNoInteractions(users,refresh,googleProfiles);
    }
    @Test void invalidTokenCannotCreateASession() throws Exception {
        ReflectionTestUtils.setField(google,"verifier",verifier);
        assertThrows(ApiException.class,()->google.login(googleRequest()));verifyNoInteractions(users,refresh);
    }
    @Test void firstGoogleStudentSignupInitializesAvatarOnceAndLaterLoginsPreserveIt() throws Exception {
        String picture = "https://lh3.googleusercontent.com/a/synthetic-avatar";
        googlePayload("newpupil@gmail.com",true).set("picture", picture);
        var request=googleRequest(); request.setRole("STUDENT"); request.setGradeLevel(3);
        UUID id=UUID.randomUUID();
        when(students.saveAndFlush(any(Student.class))).thenAnswer(invocation -> {
            Student created=invocation.getArgument(0); created.setId(id); return created;
        });
        google.login(request);
        verify(profiles).initialize(id);
        verify(profiles).captureGoogleAvatar(id, picture);
        var existing=new Student(); existing.setId(id); existing.setEmail("newpupil@gmail.com"); existing.setRole("STUDENT"); existing.setActive(true);
        when(users.findByGoogleSubject("verified-subject")).thenReturn(Optional.of(existing));
        google.login(request);
        verify(profiles,times(1)).initialize(id);
        verify(profiles, times(2)).captureGoogleAvatar(id, picture);
        verify(students,times(1)).saveAndFlush(any(Student.class));
        verifyNoInteractions(googleProfiles);
    }

    @Test void linkedStudentWithoutPictureClaimUsesGoogleProfileForVerifiedSubject() throws Exception {
        googlePayload("known@gmail.com", true);
        var student = new Student();
        student.setId(UUID.randomUUID());
        student.setEmail("known@gmail.com");
        student.setRole("STUDENT");
        student.setActive(true);
        when(users.findByGoogleSubject("verified-subject")).thenReturn(Optional.of(student));
        String picture = "https://lh3.googleusercontent.com/a/synthetic-avatar";
        when(googleProfiles.avatar("profile-token", "verified-subject")).thenReturn(picture);
        var request = googleRequest();
        request.setProfileAccessToken("profile-token");

        google.login(request);

        verify(profiles).captureGoogleAvatar(student.getId(), picture);
        verify(refresh).createSession(student.getId());
    }

    @Test void firstFacebookStudentSignupInitializesAvatarOnce() throws Exception {
        var firebase=mock(FirebaseAuth.class); var token=mock(FirebaseToken.class);
        var service=new FacebookAuthService(users,students,teachers,encoder,refresh,profiles,true,"test-project");
        ReflectionTestUtils.setField(service,"firebaseAuth",firebase);
        var request=new FacebookLoginRequest(); request.setCredential("test-credential"); request.setRole("STUDENT"); request.setGradeLevel(3);
        when(firebase.verifyIdToken("test-credential",true)).thenReturn(token);
        when(token.getClaims()).thenReturn(Map.of("firebase",Map.of("sign_in_provider","facebook.com")));
        when(token.getUid()).thenReturn("new-facebook-subject"); when(token.getEmail()).thenReturn("newpupil@example.test"); when(token.isEmailVerified()).thenReturn(true);
        UUID id=UUID.randomUUID();
        when(students.saveAndFlush(any(Student.class))).thenAnswer(invocation -> {
            Student created=invocation.getArgument(0); created.setId(id); return created;
        });
        service.login(request);
        verify(profiles).initialize(id);
    }
    @Test void requestedTeacherRoleCannotPromoteAnExistingStudent() throws Exception {
        googlePayload("known@gmail.com",true);
        var pupil=new Student();pupil.setId(UUID.randomUUID());pupil.setEmail("known@gmail.com");pupil.setRole("STUDENT");pupil.setActive(true);
        when(users.findByGoogleSubject("verified-subject")).thenReturn(Optional.of(pupil));
        google.login(googleRequest());verify(refresh).createSession(pupil.getId());
    }
    @Test void disabledAccountCannotReceiveTokens() throws Exception {
        googlePayload("known@gmail.com",true);
        var pupil=new Student();pupil.setEmail("known@gmail.com");pupil.setRole("STUDENT");pupil.setActive(false);
        when(users.findByGoogleSubject("verified-subject")).thenReturn(Optional.of(pupil));
        assertThrows(ApiException.class,()->google.login(googleRequest()));verifyNoInteractions(refresh, profiles);
    }
    @Test void facebookRejectsOtherProvidersAndUnverifiedNewEmailsWithoutLinkingByEmail() throws Exception {
        var firebase=mock(FirebaseAuth.class);var token=mock(FirebaseToken.class);
        var service=new FacebookAuthService(users,students,teachers,encoder,refresh,profiles,true,"test-project");
        ReflectionTestUtils.setField(service,"firebaseAuth",firebase);
        var request=new FacebookLoginRequest();request.setCredential("test-credential");request.setRole("STUDENT");request.setGradeLevel(3);
        when(firebase.verifyIdToken("test-credential",true)).thenReturn(token);
        when(token.getClaims()).thenReturn(Map.of("firebase",Map.of("sign_in_provider","password")));
        assertThrows(ApiException.class,()->service.login(request));verifyNoInteractions(users);
        when(token.getClaims()).thenReturn(Map.of("firebase",Map.of("sign_in_provider","facebook.com")));
        when(token.getUid()).thenReturn("facebook-subject");when(token.getEmail()).thenReturn("known@example.test");
        assertThrows(ApiException.class,()->service.login(request));
        verify(users,never()).findByEmail(anyString());verifyNoInteractions(refresh);
        when(token.isEmailVerified()).thenReturn(true);when(users.findByEmail("known@example.test")).thenReturn(Optional.of(new User()));
        assertThrows(ApiException.class,()->service.login(request));verify(users,never()).save(any());
    }
}
