package com.mathvisionkids.api.quiz;

import java.util.*;
import java.security.MessageDigest;

/** Non-secret identity of the class actually loaded by this process, not the disk checkout. */
public final class QuizRuntimeIdentity {
    public static final String INSTANCE=UUID.randomUUID().toString();
    public static final String CLASS_HASH=classHash();
    private static String classHash() {
        try(var stream=QuizMath.class.getResourceAsStream("QuizMath.class")) {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(stream.readAllBytes()));
        } catch(Exception ex) { throw new IllegalStateException("Cannot identify Quiz runtime",ex); }
    }
    public static Map<String,Object> view() { return Map.of("instance",INSTANCE,"pid",ProcessHandle.current().pid(),"generatorVersion",QuizMath.VERSION,"generatorClassHash",CLASS_HASH); }
}
