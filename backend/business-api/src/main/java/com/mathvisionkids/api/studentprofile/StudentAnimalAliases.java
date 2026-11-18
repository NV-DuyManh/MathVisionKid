package com.mathvisionkids.api.studentprofile;

import java.util.List;
import java.util.Set;
import java.util.concurrent.ThreadLocalRandom;

final class StudentAnimalAliases {
    static final List<String> ANIMALS = List.of(
            "Sư Tử", "Hổ", "Báo Đốm", "Báo Tuyết", "Gấu Trúc", "Gấu Nâu", "Gấu Bắc Cực", "Cáo Đỏ",
            "Sói Xám", "Hươu Sao", "Nai", "Tuần Lộc", "Voi", "Tê Giác", "Hà Mã", "Ngựa Vằn",
            "Hươu Cao Cổ", "Lạc Đà", "Lạc Đà Không Bướu", "Kangaroo", "Koala", "Thỏ", "Sóc", "Nhím",
            "Rái Cá", "Hải Ly", "Chồn", "Cầy Mangut", "Mèo Rừng", "Linh Miêu", "Bò Rừng", "Dê Núi",
            "Cừu", "Ngựa", "Lừa", "Khỉ", "Vượn", "Đười Ươi", "Tinh Tinh", "Vượn Cáo",
            "Cá Heo", "Cá Voi", "Hải Cẩu", "Sư Tử Biển", "Hải Mã", "Chim Cánh Cụt", "Đại Bàng", "Cú Mèo",
            "Chim Sẻ", "Chim Én", "Chim Công", "Hồng Hạc", "Bồ Câu", "Vẹt", "Chim Gõ Kiến", "Bói Cá",
            "Thiên Nga", "Vịt", "Ngỗng", "Rùa", "Tắc Kè", "Kỳ Nhông", "Ếch", "Cá Ngựa",
            "Cá Hề", "Cá Đuối", "Bạch Tuộc", "Sao Biển", "Bướm", "Chuồn Chuồn", "Bọ Rùa", "Ong");

    static String next(Set<String> used) {
        for (int suffix = 1; ; suffix++) {
            String ending = suffix == 1 ? "" : " " + suffix;
            var available = ANIMALS.stream().map(name -> name + ending).filter(name -> !used.contains(name)).toList();
            if (!available.isEmpty()) return available.get(ThreadLocalRandom.current().nextInt(available.size()));
        }
    }

    private StudentAnimalAliases() {}
}
