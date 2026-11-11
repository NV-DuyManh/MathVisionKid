package com.mathvisionkids.api.quiz;

import java.text.Normalizer;
import java.util.*;
import java.util.regex.Pattern;

/** Versioned validators form the supported taxonomy. Unrecognised prose fails closed. */
public final class QuizMath {
    public static final String VERSION = "confirmed-problem-v11";
    public static final String REMAINDER = "FRACTION_FIND_TOTAL_FROM_REMAINDER";
    public static final String DIGIT_APPEND = "DIGIT_APPEND_FIND_ORIGINAL_NUMBER";
    public static final String DIGIT_APPEND_SKILL = "RECOVER_ORIGINAL_NUMBER_FROM_DIGIT_APPEND";
    static final String PURCHASE = "UNIT_PRICE_FIND_CASH";
    static final String CLASS_COMPLEMENT = "FRACTION_FIND_CLASS_COMPLEMENT";
    static final String FOUNDATION_REVIEW = "FOUNDATION_REVIEW";
    public record Verified(String code, String name, String skill, int grade, String question,
                           String unit, Rational answer, String solution, List<String> data) {}
    private static final Pattern FRACTION = Pattern.compile("(?<![\\d/])(\\d{1,3})\\s*/\\s*(\\d{1,3})(?![\\d/])");
    private static final Pattern EXPRESSION = Pattern.compile("(?:tinh(?: gia tri)?[: ]*)?(\\d{1,4}(?:/\\d{1,3})?)\\s*([+−×÷:*x-])\\s*(\\d{1,4}(?:/\\d{1,3})?)(?:\\s*=\\s*\\??|\\s*bang bao nhieu\\??)?[.?]?");
    private static final Pattern DIGIT_APPEND_P1 = Pattern.compile(
        "^(?:(?:de|bai|bai toan|cau)\\s*[:.]\\s*)?tim\\s+(?:mot\\s+)?so(?:\\s+tu\\s+nhien)?\\s+biet(?:\\s+rang)?\\s+(?:neu|khi)?\\s*(?:viet\\s+them|them)\\s+(?:chu\\s+so\\s+)?(\\d)\\s+vao\\s+(?:tan\\s+cung\\s+)?ben\\s+phai\\s+so\\s+(?:do|phai\\s+tim|ban\\s+dau|can\\s+tim)(?:\\s+(?:thi\\s+duoc|ta\\s+duoc|thi|ta|duoc))?\\s+(?:duoc\\s+)?so\\s+moi\\s+(?:lon\\s+hon|hon)\\s+so\\s+(?:phai\\s+tim|do|ban\\s+dau|da\\s+cho|cu|can\\s+tim)\\s+(\\d{1,8})(?:\\s*don\\s+vi)?[.?]?$"
    );
    private static final Pattern DIGIT_APPEND_P2 = Pattern.compile(
        "^(?:(?:de|bai|bai toan|cau)\\s*[:.]\\s*)?(?:neu|khi)?\\s*(?:viet\\s+them|them)\\s+(?:chu\\s+so\\s+)?(\\d)\\s+vao\\s+(?:tan\\s+cung\\s+)?ben\\s+phai\\s+(?:mot\\s+)?so(?:\\s+(?:do|phai\\s+tim|ban\\s+dau|tu\\s+nhien))?(?:\\s+(?:thi\\s+duoc|ta\\s+duoc|thi|ta|duoc))?\\s+(?:duoc\\s+)?so\\s+moi\\s+(?:lon\\s+hon|hon)\\s+so\\s+(?:phai\\s+tim|do|ban\\s+dau|da\\s+cho|cu|can\\s+tim)\\s+(\\d{1,8})(?:\\s*don\\s+vi)?[.;]?(?:\\s*(?:tim\\s+so\\s+do|tim\\s+so\\s+phai\\s+tim|tim\\s+so\\s+can\\s+tim|hoi\\s+so\\s+do\\s+la\\s+bao\\s+nhieu|tim\\s+mot\\s+so))?[.?]?$"
    );
    private static final String MONEY = "(?:[0-9]{1,3}(?: [0-9]{3}){1,2}|[0-9]{1,9})";
    private static final Pattern CHOICE_LABEL = Pattern.compile("(?iU)(?<!\\w)([A-D])[.)]\\s*");
    private static final String PERSON = "[a-z]{1,18}(?: [a-z]{1,18}){0,2}";
    private static final Pattern CLASS_FRACTION = Pattern.compile(
        "lop (?<class>[1-5][a-z][0-9]?) co (?<total>[0-9]{1,3}) hoc sinh[.;] "
        + "(?:biet |trong do[,;]? )?(?:rang )?so (?:hoc sinh|ban) (?<given>nam|nu) chiem (?<share>[0-9]{1,3}/[0-9]{1,3}) "
        + "(?:tong )?so hoc sinh (?:ca |cua )?lop[.;] hoi lop (?:do|nay) co bao nhieu (?:hoc sinh|ban) (?<asked>nam|nu)[?.]?"
    );
    private static final Pattern PURCHASE_SHORTAGE = Pattern.compile(
        "(?<first>" + PERSON + ") va (?<second>" + PERSON + ") cung vao (?:mot )?cua hang [a-z ]{1,40}\\. "
        + "\\k<first> mua (?<count>[0-9]{1,3}) (?<item>(?:quyen|cuon|bong|cay|chiec|hop|tui|goi|chai|cai) [a-z]{1,18}(?: [a-z]{1,18}){0,2})"
        + " (?:het|voi tong gia) (?<paid>" + MONEY + ") dong\\. "
        + "\\k<second> muon mua (?<wanted>[0-9]{1,3}) \\k<item> (?:giong|nhu) (?:cua )?\\k<first>,? nhung (?:con )?thieu (?<shortage>" + MONEY + ") dong\\. "
        + "hoi \\k<second> (?:dang )?co bao nhieu tien[?.]?"
    );
    static String plain(String text) {
        // Explicit fraction bars only: bare digits on separate lines remain ambiguous.
        return Normalizer.normalize(text.toLowerCase(Locale.ROOT), Normalizer.Form.NFD).replaceAll("\\p{M}", "").replace('đ', 'd')
                .replaceAll("[⁄∕]", "/").replaceAll("\\(\\s*(\\d{1,3})\\s*\\)\\s*/\\s*\\(\\s*(\\d{1,3})\\s*\\)", "$1/$2")
                .replaceAll("\\(\\s*(\\d{1,3})\\s*/\\s*(\\d{1,3})\\s*\\)", "$1/$2")
                .replaceAll("\\s*/\\s*", "/").replaceAll("[\\p{Z}\\s]+", " ").strip();
    }
    public static Optional<Verified> classify(String problem, boolean confirmed) {
        if (!confirmed || problem == null || problem.length() > 4000 || problem.contains("[?]") || problem.contains("\uFFFD")) return Optional.empty();
        try {
            String text = plain(problem);
            var expression = EXPRESSION.matcher(text);
            if (expression.matches()) return Optional.of(expression(problem, expression.group(1), expression.group(2), expression.group(3)));
            var digitAppendMatch = digitAppend(problem, text);
            if (digitAppendMatch.isPresent()) return digitAppendMatch;
            var purchase = purchase(problem, text);
            if (purchase.isPresent()) return purchase;
            var classFraction = classFraction(problem, text);
            if (classFraction.isPresent()) return classFraction;
            return remainder(problem, text);
        } catch (IllegalArgumentException | ArithmeticException ex) { return Optional.empty(); }
    }
    /** Full confirmed text is the input. Topic/skill labels are outputs, never a prerequisite. */
    public static Verified generateFromConfirmed(String confirmedProblemText, Random random) {
        return generate(analyzeConfirmed(confirmedProblemText).orElseThrow(UnsupportedProblem::new), random);
    }
    public static class UnsupportedProblem extends IllegalArgumentException {}
    public static Optional<Verified> analyzeConfirmed(String problem) {
        if (problem == null || problem.length() > 4000 || problem.contains("[?]") || problem.contains("\uFFFD")) return Optional.empty();
        // Exam score/page decoration is not mathematical data. Preserve the original string in storage.
        String mathematicalText=problem.replaceAll("[\\u200B-\\u200D\\uFEFF]", "")
                .replaceAll("(?iu)\\s*\\(\\s*\\d+(?:[.,]\\d+)?\\s*điểm\\s*\\)\\s*[.]?\\s*$", "").strip();
        // A single exercise heading/score does not change the mathematical task.
        mathematicalText=mathematicalText.replaceFirst("(?iu)^(?:câu|bài)\\s+\\d+\\s*[.):]?\\s*(?:\\(\\s*\\d+(?:[.,]\\d+)?\\s*điểm\\s*\\)\\s*)?", "");
        // An ordered A-D question is one task. Check every option
        // against the exact calculation before offering a related exercise.
        var choices=CHOICE_LABEL.matcher(mathematicalText);
        var positions=new ArrayList<Integer>(); var ends=new ArrayList<Integer>(); var labels=new StringBuilder();
        while(choices.find()) { labels.append(choices.group(1).toUpperCase(Locale.ROOT)); positions.add(choices.start()); ends.add(choices.end()); }
        if(!positions.isEmpty()) {
            if(!labels.toString().equals("ABCD")) return Optional.empty();
            String stem=mathematicalText.substring(0,positions.get(0)).strip();
            stem=stem.replaceFirst("(?iu)^kết quả (?:của )?phép tính\\s*", "Tính: ")
                    .replaceFirst("(?iu)\\s+là\\s*[:?]$", "");
            var checked=classify(stem,true);
            if(checked.isEmpty()) return Optional.empty();
            try {
                var values=new ArrayList<Rational>();
                var task = checked.get();
                for (int i = 0; i < 4; i++) {
                    String option = plain(mathematicalText.substring(ends.get(i), i == 3 ? mathematicalText.length() : positions.get(i + 1)));
                    if (PURCHASE.equals(task.code()) || CLASS_COMPLEMENT.equals(task.code())) {
                        option = option.replaceFirst(" " + Pattern.quote(plain(task.unit())) + "$", "");
                        if (!option.matches(MONEY)) return Optional.empty();
                        values.add(Rational.of(money(option)));
                    } else {
                        values.add(Rational.parse(option));
                    }
                }
                if (new HashSet<>(values).size() != 4 || values.stream().filter(task.answer()::equals).count() != 1) return Optional.empty();
                if (!PURCHASE.equals(task.code()) && !CLASS_COMPLEMENT.equals(task.code())) return checked;
                return Optional.of(new Verified(task.code(), task.name(), task.skill(), task.grade(), mathematicalText,
                        task.unit(), task.answer(), task.solution(), task.data()));
            } catch(IllegalArgumentException | ArithmeticException ex) { return Optional.empty(); }
        }
        var strict=classify(mathematicalText,true);
        if(strict.isPresent()) return strict;
        // Parse the mathematical clauses separately, rather than requiring one whole-sentence template.
        try {
            var shares = relatedShares(problem,plain(mathematicalText));
            if (shares.isPresent()) return shares;
            return digitAppend(problem, plain(mathematicalText));
        }
        catch (IllegalArgumentException | ArithmeticException ex) { return Optional.empty(); }
    }
    private static Optional<Verified> digitAppend(String original, String text) {
        var m1 = DIGIT_APPEND_P1.matcher(text);
        var m = m1.matches() ? m1 : DIGIT_APPEND_P2.matcher(text);
        if (!m.matches()) return Optional.empty();
        int d = Integer.parseInt(m.group(1));
        long D = Long.parseLong(m.group(2));
        if (d < 0 || d > 9 || D <= d || (D - d) % 9 != 0) return Optional.empty();
        long x = (D - d) / 9;
        if (x <= 0 || x > 1_000_000) return Optional.empty();
        String solution = "Khi viết thêm chữ số " + d + " vào bên phải một số thì số mới gấp 10 lần số ban đầu cộng thêm " + d + " đơn vị.\n"
                + "Coi số cần tìm là 1 phần thì số mới gồm 10 phần như thế và " + d + " đơn vị.\n"
                + "Hiệu số phần bằng nhau là: 10 − 1 = 9 (phần).\n"
                + "9 lần số cần tìm là: " + D + " − " + d + " = " + (D - d) + ".\n"
                + "Số cần tìm là: " + (D - d) + " ÷ 9 = " + x + ".\n"
                + "Đáp số: " + x + ".";
        return Optional.of(new Verified(DIGIT_APPEND, "Tìm số khi viết thêm chữ số vào bên phải", DIGIT_APPEND_SKILL, 5,
                original, "", Rational.of(x), solution, List.of(String.valueOf(d), String.valueOf(D), String.valueOf(x))));
    }
    private static String shareSubject() {
        String person="(?:ban|be|bac|co|chu) [a-z]{1,20}(?: [a-z]{1,20}){0,3}";
        String place="(?:vuon(?: cay)?|thu vien|hop|gio|lop)(?: (?:nha|cua) "+person+")?";
        return "(?:trong )?(?:(?:mot )?"+place+"|"+person+")";
    }
    private static String shareIntro(String unit) {
        return shareSubject()+" co (?:mot so (?:quyen |cuon |vien )?"+unit+"[.;] trong do[,;]? )?";
    }
    private static String totalQuestion(String counter) {
        return "(?:"+shareSubject()+" )?(?:co )?(?:tat ca|tong cong|tong so) bao nhieu "+counter;
    }
    private static String[] shareContext(String label) {
        label=label.replaceFirst("^(?:trong )?(?:mot )?", "");
        if(label.matches("(?:ban|be|bac|co|chu) .*")) return new String[]{null,label};
        String[] parts=label.split(" (?:nha|cua) ",2);
        return new String[]{parts[0].replaceFirst(" cay$",""),parts.length>1?parts[1]:null};
    }
    private static boolean sameShareContext(String text,String question) {
        var stated=Pattern.compile("^("+shareSubject()+") co ").matcher(text);
        if(!stated.find()) return false;
        var targets=new ArrayList<String>();
        String asked=question.replaceFirst("(?:^| )(?:co )?(?:tat ca|tong cong|tong so)(?: |$).*", "").strip();
        if(!asked.isEmpty()) targets.add(asked);
        var countPlace=Pattern.compile(" co trong ([a-z ]{1,70}) la [0-9]").matcher(text);
        if(countPlace.find()) targets.add(countPlace.group(1));
        String[] source=shareContext(stated.group(1));
        for(String target:targets) {
            if(!target.matches(shareSubject())) return false;
            String[] scope=shareContext(target);
            if(scope[0]!=null&&!scope[0].equals(source[0]) || scope[1]!=null&&!scope[1].equals(source[1])) return false;
        }
        return true;
    }
    private static Optional<Verified> relatedShares(String original, String text) {
        if(Pattern.compile("\\b(khong|chua|them|bot|mat|sau khi|truoc khi|chet|hon|kem)\\b").matcher(text).find()) return Optional.empty();
        var fractions=FRACTION.matcher(text);
        if(fractions.results().count()!=2) return Optional.empty();
        var share=Pattern.compile("(\\d{1,3}/\\d{1,3}) (?:tong )?so (cay|sach|keo|vien bi|bong hoa|qua bong) (?:la|gom) ([a-z ]{2,70}?)(?=[,;.]| va )")
                .matcher(text);
        var amounts=new ArrayList<Rational>(); var names=new ArrayList<String>(); String unit=null;
        int end=0;
        while(share.find()) {
            String between=text.substring(end,share.start());
            if(amounts.isEmpty() ? !between.matches(shareIntro(share.group(2))) : !between.matches("[,;. ]*(?:va )?")) return Optional.empty();
            if(unit!=null && !unit.equals(share.group(2))) return Optional.empty();
            unit=share.group(2); amounts.add(Rational.parse(share.group(1))); names.add(share.group(3).strip()); end=share.end();
        }
        if(amounts.size()!=2 || names.get(0).equals(names.get(1))) return Optional.empty();
        var rest=Pattern.compile("(?:so [a-z ]+ )?con lai (?:la|gom) ([a-z ]{2,70}?)[.;]").matcher(text);
        if(!rest.find(end)) return Optional.empty();
        if(!text.substring(end,rest.start()).matches("[,;. ]*(?:va )?")) return Optional.empty();
        String category=rest.group(1).strip();
        var allNames=new ArrayList<>(names); allNames.add(category);
        for(String name:allNames) {
            if(Pattern.compile("\\b(va|con|sau|truoc)\\b").matcher(name).find()) return Optional.empty();
            for(String other:allNames) if(!name.equals(other) && name.startsWith(other+" ")) return Optional.empty();
        }
        for(String name:names) if(category.equals(name) || category.startsWith(name+" ") || name.startsWith(category+" ")) return Optional.empty();
        String categoryPrefix=switch(unit) {case "cay"->"cay ";case "sach"->"sach ";case "keo"->"keo ";case "vien bi"->"bi ";case "bong hoa"->"hoa ";default->"bong ";};
        if(!category.startsWith(categoryPrefix) || names.stream().anyMatch(n -> !n.startsWith(categoryPrefix))) return Optional.empty();
        String counter=switch(unit){case "sach"->"(?:quyen sach|quyen|sach)";case "keo"->"(?:vien keo|vien|keo)";default->unit;};
        String tail=text.substring(rest.end()).strip();
        var count=Pattern.compile("(?:biet (?:rang )?)?(?:(?:so )?"+Pattern.quote(category)+" (?:co trong [a-z ]+ la|la|co) (\\d{1,5}) "+counter+"|co (\\d{1,5}) (?:quyen |vien )?"+Pattern.quote(category)+")[.;] (?:hoi |tinh )([a-z ]+?)\\??[.]?$").matcher(tail);
        if(!count.matches()) return Optional.empty();
        String question=count.group(3);
        if(names.stream().anyMatch(question::contains) || question.contains(category) || !question.matches(totalQuestion(counter)) || !sameShareContext(text,question)) return Optional.empty();
        Rational a=amounts.get(0),b=amounts.get(1),n=Rational.parse(count.group(1)!=null?count.group(1):count.group(2));
        Rational total=n.divide(Rational.ONE.subtract(a.add(b)));
        if(total.numerator().intValueExact()>10000) return Optional.empty();
        String display=switch(unit){case "cay"->"cây";case "sach"->"quyển sách";case "keo"->"viên kẹo";case "vien bi"->"viên bi";case "bong hoa"->"bông hoa";default->"quả bóng";};
        return Optional.of(remainderVerified(original,display,a,b,n,total));
    }
    private static Optional<Verified> remainder(String question, String text) {
        // Only two explicit fractions of the SAME population, a disjoint remainder,
        // one remaining integer count, and one question asking for that population.
        if (Pattern.compile("\\b(khong|chua|them|bot|mat|sau khi|truoc khi)\\b").matcher(text).find()) return Optional.empty();
        var fractions = FRACTION.matcher(text); var values = new ArrayList<Rational>();
        while (fractions.find()) values.add(Rational.parse(fractions.group()));
        if (values.size() != 2) return Optional.empty();
        String unit = null;
        for (String candidate : List.of("cay", "sach", "keo", "vien bi", "bong hoa", "qua bong")) {
            if (Pattern.compile("\\d\\s+so " + candidate + "\\b").matcher(text).results().count() == 2) { unit = candidate; break; }
        }
        if (unit == null) return Optional.empty();
        // Each known share has a category; do not interpret comparative or sequential fractions as shares of the original total.
        String category = "[a-z ]{2,70}";
        String fraction = "\\d{1,3}\\s*/\\s*\\d{1,3}";
        String prefix = shareIntro(unit);
        String counter=switch(unit) { case "sach" -> "quyen(?: sach)?"; case "keo" -> "vien(?: keo)?"; default -> unit; };
        String grammar = prefix + fraction + " so " + unit + " la (" + category + ")[,;.] ?(?:va )?"
                + fraction + " so " + unit + " la (" + category + ")[,;.] ?(?:so " + unit + " )?con lai la (" + category + ")\\. "
                + "biet (?:rang )?([^.?]{1,120})\\. "
                + "hoi ((?:"+shareSubject()+" )?(?:co )?(?:tat ca|tong cong|tong so) )bao nhieu " + counter + "\\??";
        var match = Pattern.compile(grammar).matcher(text);
        if (!match.matches()) return Optional.empty();
        if (!sameShareContext(text,match.group(5))) return Optional.empty();
        var categories = new HashSet<String>();
        for (int i=1;i<=3;i++) {
            String value=match.group(i).strip();
            if (!categories.add(value) || Pattern.compile("\\b(khong|hon|kem|sau|truoc|con|nhieu|it|va)\\b").matcher(value).find()) return Optional.empty();
            if (match.group(5).contains(value)) return Optional.empty();
            String categoryPrefix=switch(unit) { case "cay" -> "cay "; case "sach" -> "sach "; case "keo" -> "keo "; case "vien bi" -> "bi "; case "bong hoa" -> "hoa "; default -> "bong "; };
            if (!value.startsWith(categoryPrefix)) return Optional.empty();
        }
        for (String a : categories) for (String b : categories)
            if (!a.equals(b) && a.startsWith(b + " ")) return Optional.empty();
        String remainderName=Pattern.quote(match.group(3).strip());
        String location="(?:co trong (?:vuon|thu vien|hop|gio|lop)(?: [a-z ]{1,40})? la|la|co)";
        var before=Pattern.compile("(?:so )?" + remainderName + " " + location + " (\\d{1,5}) " + counter).matcher(match.group(4));
        var after=Pattern.compile("co (\\d{1,5}) (?:quyen |vien )?" + remainderName).matcher(match.group(4));
        String amount;
        if (before.matches()) amount=before.group(1);
        else if (after.matches()) amount=after.group(1);
        else return Optional.empty();
        Rational a = values.get(0), b = values.get(1), remaining = Rational.ONE.subtract(a.add(b));
        Rational count = Rational.parse(amount);
        if (!a.positive() || !b.positive() || !remaining.positive() || !count.positive()) return Optional.empty();
        Rational total = count.divide(remaining);
        if (!total.integer() || !total.multiply(a).integer() || !total.multiply(b).integer()
                || total.numerator().intValueExact() > 10000) return Optional.empty();
        String displayUnit = switch (unit) { case "cay" -> "cây"; case "sach" -> "quyển sách"; case "keo" -> "viên kẹo"; case "vien bi" -> "viên bi"; case "bong hoa" -> "bông hoa"; default -> "quả bóng"; };
        return Optional.of(remainderVerified(question, displayUnit, a, b, count, total));
    }
    static Verified remainderVerified(String question, String unit, Rational a, Rational b, Rational count, Rational expected) {
        Rational sum = a.add(b), rest = Rational.ONE.subtract(sum);
        if (!a.positive() || !b.positive() || !rest.positive() || !count.positive()) throw new IllegalArgumentException();
        Rational total = count.divide(rest);
        if (!total.equals(expected) || !total.integer() || !total.multiply(a).integer() || !total.multiply(b).integer()) throw new IllegalArgumentException();
        String solution = "Cộng hai phần đã biết: " + a + " + " + b + " = " + sum + ".\n"
                + "Phần còn lại là: 1 − " + sum + " = " + rest + ".\n"
                + "Vì " + rest + " số lượng là " + count + " " + unit + ", toàn bộ có: " + count + " ÷ (" + rest + ") = " + total + " " + unit + ".";
        return new Verified(REMAINDER, "Tìm tổng khi biết phần còn lại", "ADD_SHARES_FIND_REMAINDER_RECOVER_WHOLE", 4,
                question, unit, total, solution, List.of(a.toString(), b.toString(), count.toString()));
    }
    static Verified expression(String question, String left, String operator, String right) {
        Rational a = Rational.parse(left), b = Rational.parse(right);
        String op = switch (operator) { case "-", "−" -> "−"; case "x", "*", "×" -> "×"; case ":", "÷" -> "÷"; default -> "+"; };
        boolean fractions = left.contains("/") || right.contains("/");
        if (fractions && !List.of("+", "−").contains(op)) throw new IllegalArgumentException();
        Rational answer = switch (op) { case "+" -> a.add(b); case "−" -> a.subtract(b); case "×" -> a.multiply(b); default -> a.divide(b); };
        if (!a.positive() || !b.positive() || !answer.positive() || (!fractions && !answer.integer())) throw new IllegalArgumentException();
        return new Verified(fractions ? "FRACTION_ADDITION_SUBTRACTION" : List.of("×", "÷").contains(op) ? "MULTIPLICATION_DIVISION" : "ARITHMETIC_ADDITION_SUBTRACTION",
                fractions ? "Cộng, trừ phân số" : List.of("×", "÷").contains(op) ? "Nhân, chia số tự nhiên" : "Cộng, trừ số tự nhiên",
                "COMPUTE_" + switch(op) { case "+" -> "SUM"; case "−" -> "DIFFERENCE"; case "×" -> "PRODUCT"; default -> "QUOTIENT"; },
                fractions ? 4 : arithmeticGrade(op,a,b,answer),
                question, "", answer, "Ta tính: " + a + " " + op + " " + b + " = " + answer + ".", List.of(left, op, right));
    }
    private static int arithmeticGrade(String op, Rational a, Rational b, Rational answer) {
        int left=a.numerator().intValueExact(), right=b.numerator().intValueExact(), result=answer.numerator().intValueExact();
        if (op.equals("×")) {
            if (Math.min(left,right)<=5 && Math.max(left,right)<=10) return 2;
            return Math.min(left,right)<=9 ? 3 : 4;
        }
        if (op.equals("÷")) {
            if (right<=5 && result<=10) return 2;
            return right<=9 ? 3 : 4;
        }
        int largest=Math.max(Math.max(left,right),result);
        return largest<=20 ? 1 : largest<=100 ? 2 : 3;
    }

    private static long money(String text) {
        return Long.parseLong(text.replace(" ", ""));
    }

    private static Optional<Verified> classFraction(String original, String text) {
        var match = CLASS_FRACTION.matcher(text);
        if (!match.matches() || match.group("given").equals(match.group("asked"))) return Optional.empty();
        long total = Long.parseLong(match.group("total"));
        Rational share = Rational.parse(match.group("share"));
        if (total < 2 || total > 100 || !share.positive() || !Rational.ONE.subtract(share).positive()) return Optional.empty();
        Rational known = Rational.of(total).multiply(share);
        if (!known.integer()) return Optional.empty();
        Rational answer = Rational.of(total).subtract(known);
        String given = match.group("given").equals("nu") ? "nữ" : "nam";
        String asked = match.group("asked").equals("nu") ? "nữ" : "nam";
        String solution = "Số học sinh " + given + " là " + total + " × " + share + " = " + known + " học sinh.\n"
                + "Số học sinh " + asked + " là " + total + " − " + known + " = " + answer + " học sinh.\n"
                + "Đáp số: " + answer + " học sinh.";
        return Optional.of(new Verified(CLASS_COMPLEMENT, "Tìm phần còn lại của một số", "FRACTION_OF_TOTAL_THEN_SUBTRACT", 4,
                original, "học sinh", answer, solution, List.of(match.group("class"), Long.toString(total), share.toString(), match.group("given"))));
    }

    private static Verified classFractionVariant(Verified source, Random random, Set<String> excludedAnswers) {
        var variants = new ArrayList<Verified>();
        // Multiples of the denominator keep both groups whole and the classroom size realistic.
        for (int denominator = 3; denominator <= 8; denominator++) {
            for (int numerator = 1; numerator < denominator; numerator++) {
                var share = Rational.parse(numerator + "/" + denominator);
                if (share.toString().equals(source.data().get(2))) continue;
                for (int total = 24; total <= 50; total++) {
                    if (Integer.toString(total).equals(source.data().get(1)) || !Rational.of(total).multiply(share).integer()) continue;
                    String className = source.data().getFirst().equals("4b") ? "4C" : "4B";
                    String given = source.data().get(3).equals("nu") ? "nam" : "nữ";
                    String asked = given.equals("nam") ? "nữ" : "nam";
                    String question = "Lớp " + className + " có " + total + " học sinh. Biết số học sinh " + given
                            + " chiếm " + share + " số học sinh cả lớp. Hỏi lớp đó có bao nhiêu học sinh " + asked + "?";
                    var candidate = classFraction(question, plain(question)).orElseThrow();
                    if (candidate.answer().equals(source.answer()) || excludedAnswers.contains(candidate.answer().toString())) continue;
                    variants.add(candidate);
                }
            }
        }
        if (variants.isEmpty()) throw new IllegalArgumentException("No validated class fraction variant");
        var chosen = variants.get(random.nextInt(variants.size()));
        if (!CHOICE_LABEL.matcher(source.question()).find()) return chosen;
        long total = Long.parseLong(chosen.data().get(1));
        long answer = chosen.answer().numerator().longValueExact();
        var options = new LinkedHashSet<>(List.of(answer, total - answer, total));
        for (long value = answer + 1; options.size() < 4; value++) options.add(value);
        var shuffled = new ArrayList<>(options);
        Collections.shuffle(shuffled, random);
        String question = chosen.question();
        for (int i = 0; i < shuffled.size(); i++) question += "\n" + (char) ('A' + i) + ". " + shuffled.get(i) + " học sinh";
        return analyzeConfirmed(question).orElseThrow(() -> new IllegalArgumentException("Invalid class fraction choices"));
    }

    private static String moneyText(long amount) {
        return String.format(Locale.ROOT, "%,d", amount).replace(',', ' ');
    }

    private static Optional<Verified> purchase(String original, String text) {
        var match = PURCHASE_SHORTAGE.matcher(text);
        if (!match.matches() || match.group("first").equals(match.group("second"))) return Optional.empty();
        int count = Integer.parseInt(match.group("count"));
        int wanted = Integer.parseInt(match.group("wanted"));
        long paid = money(match.group("paid"));
        long shortage = money(match.group("shortage"));
        if (count < 2 || wanted < 2 || paid <= 0 || paid % count != 0 || shortage <= 0) return Optional.empty();
        long price = paid / count;
        long total = price * wanted;
        long cash = total - shortage;
        if (cash <= 0 || total > 999_999_999) return Optional.empty();
        String solution = "Giá một món là " + moneyText(paid) + " ÷ " + count + " = " + moneyText(price) + " đồng.\n"
                + "Số tiền cần để mua " + wanted + " món là " + moneyText(price) + " × " + wanted + " = " + moneyText(total) + " đồng.\n"
                + "Vì còn thiếu " + moneyText(shortage) + " đồng, số tiền đang có là "
                + moneyText(total) + " − " + moneyText(shortage) + " = " + moneyText(cash) + " đồng.\n"
                + "Đáp số: " + moneyText(cash) + " đồng.";
        return Optional.of(new Verified(PURCHASE, "Tính số tiền đang có", "UNIT_PRICE_MULTIPLY_SUBTRACT", 4,
                original, "đồng", Rational.of(cash), solution,
                List.of(match.group("item"), match.group("count"), Long.toString(price), match.group("wanted"), Long.toString(shortage))));
    }

    private static Verified purchaseVariant(Verified source, Random random, Set<String> excludedAnswers) {
        int sourceCount = Integer.parseInt(source.data().get(1));
        long sourcePrice = Long.parseLong(source.data().get(2));
        int sourceWanted = Integer.parseInt(source.data().get(3));
        long sourceShortage = Long.parseLong(source.data().get(4));
        String[] items = {"bông hoa", "chiếc bánh", "quyển vở"};
        String[] places = {"hoa", "bánh", "văn phòng phẩm"};
        String[] foldedItems = {"bong hoa", "chiec banh", "quyen vo"};
        boolean withChoices = CHOICE_LABEL.matcher(source.question()).find();
        for (int attempt = 0; attempt < 100; attempt++) {
            int context = random.nextInt(items.length);
            if (foldedItems[context].equals(source.data().getFirst())) continue;
            int count = Math.min(999, Math.max(2, sourceCount + random.nextInt(7) - 3));
            int wanted = Math.min(999, Math.max(2, sourceWanted + random.nextInt(7) - 3));
            long price = Math.max(1, sourcePrice + (random.nextInt(7) - 3) * Math.max(1, sourcePrice / 20));
            long paid = count * price;
            long total = wanted * price;
            long shortage = Math.min(total - 2, Math.max(1, sourceShortage * (7 + random.nextInt(7)) / 10));
            long cash = total - shortage;
            if ((count == sourceCount && wanted == sourceWanted) || shortage <= 0
                    || paid > 999_999_999 || total + shortage > 999_999_999
                    || source.answer().equals(Rational.of(cash)) || excludedAnswers.contains(Long.toString(cash))) continue;
            String first = context == 0 ? "Hòa" : context == 1 ? "An" : "Linh";
            String second = context == 0 ? "Long" : context == 1 ? "Vy" : "Bình";
            String item = items[context];
            String question = first + " và " + second + " cùng vào một cửa hàng " + places[context] + ". "
                    + first + " mua " + count + " " + item + " hết " + moneyText(paid) + " đồng. "
                    + second + " muốn mua " + wanted + " " + item + " như của " + first
                    + " nhưng còn thiếu " + moneyText(shortage) + " đồng. Hỏi " + second + " đang có bao nhiêu tiền?";
            if (withChoices) {
                var values = new ArrayList<>(List.of(cash, total, total + shortage, Math.max(1, cash - price)));
                Collections.shuffle(values, random);
                for (int i = 0; i < values.size(); i++) {
                    question += "\n" + (char) ('A' + i) + ". " + moneyText(values.get(i)) + " đồng";
                }
            }
            var checked = analyzeConfirmed(question);
            if (checked.isPresent() && PURCHASE.equals(checked.get().code()) && checked.get().answer().equals(Rational.of(cash))) {
                return checked.get();
            }
        }
        throw new IllegalArgumentException("No validated purchase variant");
    }

    public static Verified generate(Verified source, Random random) {
        return generate(source,random,Set.of());
    }
    public static Verified generate(Verified source, Random random, Set<String> excludedAnswers) {
        if (PURCHASE.equals(source.code())) return purchaseVariant(source, random, excludedAnswers);
        if (CLASS_COMPLEMENT.equals(source.code())) return classFractionVariant(source, random, excludedAnswers);
        if (source.code().equals(DIGIT_APPEND)) {
            int currentX = Integer.parseInt(source.data().get(2));
            for (int attempt = 0; attempt < 200; attempt++) {
                int d = 1 + random.nextInt(9);
                int x = 12 + random.nextInt(88); // 12 to 99
                if (x == currentX) continue;
                long D = 9L * x + d;
                String question = "Tìm một số biết rằng nếu viết thêm chữ số " + d + " vào bên phải số đó thì được số mới lớn hơn số phải tìm " + D + " đơn vị.";
                var checked = classify(question, true);
                if (checked.isPresent() && !excludedAnswers.contains(checked.get().answer().toString()) && checked.get().answer().equals(Rational.of(x)) && checked.get().code().equals(DIGIT_APPEND)) {
                    return checked.get();
                }
            }
            // Exhaust the finite supported domain before reporting that no fresh answer remains.
            for (int x=12;x<=99;x++) for (int d=1;d<=9;d++) {
                if (x == currentX) continue;
                long D = 9L * x + d;
                String question = "Tìm một số biết rằng nếu viết thêm chữ số " + d + " vào bên phải số đó thì được số mới lớn hơn số phải tìm " + D + " đơn vị.";
                var checked = classify(question, true);
                if (checked.isPresent() && !excludedAnswers.contains(checked.get().answer().toString()) && checked.get().answer().equals(Rational.of(x))) {
                    return checked.get();
                }
            }
            throw new IllegalArgumentException("No validated variant for digit append");
        }
        for (int attempt = 0; attempt < 500; attempt++) {
            Verified candidate;
            if (source.code().equals(REMAINDER)) {
                // LCM multiples guarantee every category is a positive integer.
                int da = 3 + random.nextInt(6), db = 3 + random.nextInt(6);
                Rational a = Rational.parse((1 + random.nextInt(da - 1)) + "/" + da);
                Rational b = Rational.parse((1 + random.nextInt(db - 1)) + "/" + db);
                Rational rest = Rational.ONE.subtract(a.add(b)); if (!rest.positive()) continue;
                int lcm = a.denominator().multiply(b.denominator()).divide(a.denominator().gcd(b.denominator())).intValueExact();
                Rational total = Rational.of(lcm * (2 + random.nextInt(5))), count = total.multiply(rest);
                if (total.equals(source.answer()) || source.data().contains(a.toString()) || source.data().contains(b.toString())
                        || count.toString().equals(source.data().get(2))) continue;
                candidate = remainderVariant(a,b,total,random.nextInt(3),random.nextInt(4));
                if (candidate.unit().equals(source.unit())) continue;
            } else {
                String op = source.data().get(1); boolean fractions = source.code().startsWith("FRACTION");
                int bound = Math.min(99, Math.max(5, Math.max(Rational.parse(source.data().get(0)).numerator().intValue(), Rational.parse(source.data().get(2)).numerator().intValue())));
                String a = String.valueOf(1 + random.nextInt(bound)), b = String.valueOf(1 + random.nextInt(bound));
                if (fractions) { a = (1 + random.nextInt(5)) + "/" + (2 + random.nextInt(7)); b = (1 + random.nextInt(5)) + "/" + (2 + random.nextInt(7)); }
                try { candidate = expression("Tính: " + a + " " + op + " " + b, a, op, b); } catch (IllegalArgumentException ex) { continue; }
                if (candidate.grade() > source.grade() || candidate.answer().equals(source.answer()) || candidate.data().get(0).equals(source.data().get(0)) || candidate.data().get(2).equals(source.data().get(2))) continue;
            }
            // Independently parse the generated wording back into the validator before persistence.
            var checked = classify(candidate.question(), true);
            if (checked.isPresent() && !excludedAnswers.contains(checked.get().answer().toString()) && checked.get().answer().equals(candidate.answer()) && checked.get().code().equals(source.code())) return checked.get();
        }
        if (source.code().equals(REMAINDER)) {
            // Bounded deterministic fallback, still checked against this source and the wording parser.
            for (int da=3;da<=8;da++) for (int db=3;db<=8;db++)
                for (int na=1;na<da;na++) for (int nb=1;nb<db;nb++) {
                    Rational a=Rational.parse(na+"/"+da),b=Rational.parse(nb+"/"+db);
                    if (!Rational.ONE.subtract(a.add(b)).positive()) continue;
                    int lcm=a.denominator().multiply(b.denominator()).divide(a.denominator().gcd(b.denominator())).intValueExact();
                    for (int multiplier=2;multiplier<=6;multiplier++) for(int context=0;context<3;context++) {
                        var candidate=remainderVariant(a,b,Rational.of(lcm*multiplier),context);
                        if (candidate.unit().equals(source.unit()) || candidate.answer().equals(source.answer()) || excludedAnswers.contains(candidate.answer().toString())
                            || source.data().contains(a.toString()) || source.data().contains(b.toString()) || candidate.data().get(2).equals(source.data().get(2))) continue;
                        var checked=classify(candidate.question(),true);
                        if (checked.isPresent() && checked.get().answer().equals(candidate.answer())) return checked.get();
                    }
                }
        } else {
            String op=source.data().get(1); boolean fractions=source.code().startsWith("FRACTION");
            var values=new ArrayList<String>();
            if(fractions) { for(int n=1;n<=5;n++) for(int d=2;d<=8;d++) values.add(n+"/"+d); }
            else {
                int bound=Math.min(99,Math.max(5,Math.max(Rational.parse(source.data().get(0)).numerator().intValue(),Rational.parse(source.data().get(2)).numerator().intValue())));
                for(int n=1;n<=bound;n++) values.add(String.valueOf(n));
            }
            for(String a:values) for(String b:values) {
                if(a.equals(source.data().get(0)) || b.equals(source.data().get(2))) continue;
                try {
                    var candidate=expression("Tính: "+a+" "+op+" "+b,a,op,b);
                    if(candidate.grade()<=source.grade() && !candidate.answer().equals(source.answer()) && !excludedAnswers.contains(candidate.answer().toString())) return candidate;
                } catch(IllegalArgumentException ex) { /* Invalid candidates do not enter storage. */ }
            }
        }
        throw new IllegalArgumentException("No validated variant");
    }
    private static Verified remainderVariant(Rational a,Rational b,Rational total,int context) {
        return remainderVariant(a,b,total,context,context%4);
    }
    private static Verified remainderVariant(Rational a,Rational b,Rational total,int context,int person) {
        Rational count=total.multiply(Rational.ONE.subtract(a.add(b)));
        String question,unit;
        if(context==0) {
            unit="quyển sách";
            question="Thư viện có "+a+" số sách là sách truyện, "+b+" số sách là sách khoa học, còn lại là sách tham khảo. Biết số sách tham khảo là "+count+" quyển sách. Hỏi thư viện có tất cả bao nhiêu quyển sách?";
        } else if(context==1) {
            unit="viên kẹo";
            String name=List.of("Mạnh","An","Linh","Bảo").get(person);
            question="Bé "+name+" có một số viên kẹo. Trong đó, "+a+" số kẹo là kẹo dâu, "+b+" số kẹo là kẹo cam, còn lại là kẹo chanh. Biết có "+count+" viên kẹo chanh. Hỏi bé "+name+" có tất cả bao nhiêu viên kẹo?";
        } else {
            unit="viên bi";
            question="Hộp bi có "+a+" số viên bi là bi đỏ, "+b+" số viên bi là bi xanh, còn lại là bi vàng. Biết số bi vàng là "+count+" viên bi. Hỏi hộp bi có tất cả bao nhiêu viên bi?";
        }
        return remainderVerified(question,unit,a,b,count,total);
    }
    static Rational answerInput(String input, String unit) {
        String text = input.strip().replaceAll("\\s+", " ");
        for (String suffix : List.of("đơn vị", "don vi")) {
            if (text.toLowerCase(Locale.ROOT).endsWith(" " + suffix)) {
                text = text.substring(0, text.length() - suffix.length()).strip();
                break;
            }
        }
        if (!unit.isBlank()) {
            for (String suffix : unit.equals("quyển sách") ? List.of("quyển sách", "quyển") : List.of(unit))
                if (text.toLowerCase(Locale.ROOT).endsWith(" " + suffix)) { text = text.substring(0, text.length() - suffix.length()).strip(); break; }
        }
        return Rational.parse(text);
    }
}
