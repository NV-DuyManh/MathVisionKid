# Review và tích hợp nhánh Kha — 24/10/2026

## Phạm vi

Chủ dự án yêu cầu review kỹ `Kha`, xử lý xung đột, merge vào `main` rồi push. Nền review là `main` tại `9c713cfe75672d5e2404201b9027d10143be0975`; nhánh nguồn tại `6177b83669db3309c6fe948feb91141d6242f8e7`, gồm bốn commit chưa có trên main. Review và cài dependency trong checkout riêng, không dùng node_modules của workspace đang làm dở.

Nhánh bổ sung năm trò chơi tại mục Của em, SDK 58, điều hướng/lifecycle game và gói phân phối tương đối `@mathvisionkid/training-games@0.1.2`. Không huấn luyện/thay model, đổi RBAC backend hoặc deploy dịch vụ.

## Phát hiện và xử lý

| Mức | Vấn đề | Bản sửa trong merge |
|---|---|---|
| P1 | Compose dùng image MinIO chỉ có trên máy tác giả, `pull_policy: never`, không khai báo build; máy mới không khởi động được stack | Khôi phục image public được ghim như main, bỏ Dockerfile mới không được dùng; cấu hình chuẩn hóa PostgreSQL/MinIO/Redis khớp main |
| P2 | Bốn game dùng bộ phát chỉ hỗ trợ Web Audio: có nút tiếng nhưng Android/iOS không phát hiệu ứng | Thêm adapter native bằng expo-audio và WAV PCM ngắn tạo cục bộ; web giữ controller cũ. Giới hạn bốn player đồng thời, dừng/xóa tài nguyên khi tắt tiếng, ra nền hoặc dispose; bỏ callback âm thanh của phiên cũ |
| P2 | Lỗi đọc/lưu cài đặt dùng chung thông báo với hàng đợi kết quả; nút thử lưu lại không chạy lại thao tác đã lỗi và một lần ghi kết quả thành công có thể che lỗi cài đặt | Tách lỗi cài đặt theo runtime đang mở khỏi lỗi kết quả có thể retry; bỏ nút retry sai ngữ cảnh, ghi cài đặt tuần tự và bỏ thông báo trễ sau dispose |
| P2 | Nâng SDK 58 nhưng cache video vẫn dùng `File.write()` bất đồng bộ và trả URI trước khi ghi xong | Giữ bản sửa `writeSync()` đã có trên workspace, thêm kiểm thử chặn việc công bố URI khi bytes chưa sẵn sàng |
| Tích hợp | SDK/Jest/Metro/tab trùng phạm vi với thay đổi đang làm dở | Hợp nhất cấu hình thay vì chép đè: giữ blockList runtime, hover thật, slider, test contracts, ghim React/DOM chung; chỉ dùng một jest.config.js |

Không tìm thấy blocker còn lại trong phạm vi đã kiểm tra. Các guard UUID/role, trial chỉ dành cho development, allowlist game, cô lập học sinh, callback sau dispose và chống ghi trùng được giữ nguyên. Kết quả game chỉ lưu trên thiết bị, chưa đồng bộ thành tích lên backend. Các con số kiểm thử không thay cho xác nhận trên điện thoại thật.

## Review gói phân phối

- SHA-256 archive 0.1.2: `f6a319d1b61c53cdbe1331d9812c85a9813b3ead9841eb05c3c639b657186f9e`, khớp PACKAGE_MANIFEST.
- Kiểm tra 223 mục archive và 220 hash nội bộ: khớp metadata/kích thước; không có traversal, symlink hoặc script cài đặt.
- Không phát hiện runtime network API hoặc bí mật trong gói. Storage host phân vùng theo UUID học sinh và game, giới hạn lịch sử; trial chỉ dùng bộ nhớ.
- Không sửa nội dung tarball hoặc tạo bản gameplay thứ hai. Adapter âm thanh nằm ở host. Updater không được chạy vì nó chủ động tạo/cài artifact mới ngoài yêu cầu merge.

## Kiểm chứng checkout tích hợp

| Kiểm tra | Kết quả |
|---|---|
| Cài mới từ lockfile bằng npm ci --ignore-scripts | Đạt |
| Student Jest trước sửa review | 77 suite / 925 test đạt |
| Student Jest sau sửa review | 80 suite / 937 test đạt |
| Student TypeScript | Đạt |
| Student lint | 0 lỗi, 2 cảnh báo có sẵn tại cropRotation.web.ts |
| Node web-auth/privacy contracts | 8/8 đạt |
| Metro runtime blockList | 1/1 đạt |
| Student export | Android + iOS Hermes và web tĩnh: 38 route, năm chunk game |
| Browser với module game thật | 5/5: catalog → chơi → thoát → catalog, game cũ unmount; không page error/HTTP error/failed request |
| Teacher/Admin/Portal và packages build | Đạt |
| Ba web: config/auth/API contracts | 50/50 đạt |
| Ba web: production bundle, SSO/logout/menu | 9/9 đạt |
| Dependency graph | Một React/DOM 19.3.0 dùng chung; RN 0.88.0, Router 58.0.25 |
| Docker Compose config | Dịch vụ nền tảng giữ cấu hình main; không khởi động hoặc pull dịch vụ |

Browser dùng Chromium, viewport 390×844; Race dùng 844×390. Chỉ `/me` là HTTP fixture với UUID học sinh, gameplay chạy từ export thật; không gọi đó là kiểm thử Android/Expo Go. Bộ native audio kiểm tra WAV không im lặng, thứ tự cấu hình/player và giải phóng tài nguyên qua native I/O mocks; chưa nghe xác nhận trên thiết bị vật lý. Lần browser đầu chưa chờ Race tải xong tài nguyên; đã sửa readiness của script, không sửa sản phẩm để làm test đạt.

Console browser có 9 cảnh báo BackHandler không hỗ trợ web từ gói game; không có lỗi trang chưa bắt hoặc request lỗi. Bằng chứng không khẳng định console hoàn toàn không có cảnh báo.

Build web dùng URL production mẫu trong tiến trình, không lưu env/deploy. Có cảnh báo chunk web lớn hơn 500kB. Kiểm tra Expo online gợi ý các bản vá SDK 58 mới hơn; phiên bản đã khóa khớp bảng bundledNativeModules của Expo 58.0.17 và đã được kiểm tra đóng gói. Không mở rộng lượt merge thành cập nhật toàn bộ thư viện.

## Bảo toàn workspace và Git

Trước merge đã lưu trạng thái Git, hash và bản sao 81 file nguồn/tài liệu đang thay đổi. Các phần SDK 58 giao nhau được đối chiếu/hợp nhất vào commit review; các thay đổi media, AI/OCR và backend đang dở được giữ riêng. Không dùng reset hard, force push hoặc stage toàn bộ workspace. File che tên/cắt ảnh và UI được yêu cầu giữ nguyên được kiểm tra SHA-256.

Log và bằng chứng tại `report/kha-review-20261024/`: bản cài sạch, Jest JSON, TypeScript/lint, export, web build/test, review manifest, browser JSON/ảnh và đối chiếu working tree sau merge. Chỉ báo cáo này được thêm cùng source review, không đưa node_modules, dữ liệu local hay bản sao WIP vào commit.

## Xác nhận sau khi merge vào workspace chính

- Commit merge: `84a906b9c65bc966a225bb5acd99043c04d990bf`, bao gồm toàn bộ nhánh Kha đã review. Có nhánh dự phòng cục bộ `codex/pre-kha-main-20261024` tại main trước merge.
- 57 file ngoài 24 đường dẫn giao nhau giữ nguyên SHA-256. Bản gốc 24 file SDK/cấu hình đã được hợp nhất vẫn có trong `wip-source-backup/` và scoped stash, không áp lại cấu hình cũ đè bản tích hợp.
- Sau cài dependency ở workspace chính, manifests và lockfile không phát sinh diff. Các phần media/OCR/backend đang dở vẫn chưa bị đưa vào commit này.
- Toàn bộ Student cùng các thay đổi đang dở: **86 suite / 957 test đạt**, TypeScript đạt, Android export đạt. Năm file che tên/cắt ảnh/UI bảo vệ giữ nguyên SHA-256.
- Lần kiểm tra song song export đầu có một test vượt timeout 5 giây và kéo theo một lỗi cleanup trong cùng suite; chạy lại riêng suite đạt 51/51, sau đó chạy lại toàn bộ đạt 957/957. Không tăng timeout hoặc sửa sản phẩm để bỏ qua lỗi.
- Cache type của Router ở máy cũ chưa có đường dẫn game mới; đã để Expo CLI tái sinh cache chính thức rồi chạy lại TypeScript, không ép kiểu để che lỗi.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa các blocker cụ thể và tích hợp cấu hình sẵn có với phạm vi nhỏ.
  - Applied to: bảo toàn working tree, Compose, đồng bộ dependency/Jest/Metro, cache video và adapter native không thêm thư viện.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: review lifecycle và tương tác React/React Native.
  - Applied to: điều hướng, giải phóng âm thanh, thông báo lỗi theo phiên, hover và kiểm thử bundle/game thật.
