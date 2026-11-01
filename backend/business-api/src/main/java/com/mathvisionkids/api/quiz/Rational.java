package com.mathvisionkids.api.quiz;

import java.math.BigDecimal;
import java.math.BigInteger;

/** Exact, reduced rational arithmetic. No floating point or expression evaluation. */
record Rational(BigInteger numerator, BigInteger denominator) {
    static final Rational ONE = of(1);
    Rational {
        if (denominator.signum() == 0) throw new IllegalArgumentException("Zero denominator");
        if (denominator.signum() < 0) { numerator = numerator.negate(); denominator = denominator.negate(); }
        var gcd = numerator.gcd(denominator);
        numerator = numerator.divide(gcd); denominator = denominator.divide(gcd);
    }
    static Rational of(long n) { return new Rational(BigInteger.valueOf(n), BigInteger.ONE); }
    static Rational parse(String value) {
        String text = value.strip().replace(',', '.').replaceAll("\\s*/\\s*", "/");
        if (text.length() > 40 || !text.matches("[+-]?\\d{1,12}(?:/\\d{1,12}|\\.\\d{1,8})?"))
            throw new IllegalArgumentException("Invalid number");
        if (text.contains("/")) { var parts = text.split("/"); return new Rational(new BigInteger(parts[0]), new BigInteger(parts[1])); }
        var decimal = new BigDecimal(text);
        return new Rational(decimal.unscaledValue(), BigInteger.TEN.pow(Math.max(0, decimal.scale())));
    }
    Rational add(Rational b) { return new Rational(numerator.multiply(b.denominator).add(b.numerator.multiply(denominator)), denominator.multiply(b.denominator)); }
    Rational subtract(Rational b) { return add(new Rational(b.numerator.negate(), b.denominator)); }
    Rational multiply(Rational b) { return new Rational(numerator.multiply(b.numerator), denominator.multiply(b.denominator)); }
    Rational divide(Rational b) { return new Rational(numerator.multiply(b.denominator), denominator.multiply(b.numerator)); }
    boolean positive() { return numerator.signum() > 0; }
    boolean integer() { return denominator.equals(BigInteger.ONE); }
    @Override public String toString() { return integer() ? numerator.toString() : numerator + "/" + denominator; }
}
