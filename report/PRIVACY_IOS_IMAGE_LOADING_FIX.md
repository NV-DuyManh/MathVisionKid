# Sửa privacy image loading trên iOS — 2026-10-26

## Skills Applied

- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React lifecycle, state và callback bất đồng bộ.
  - Applied to: subscribe draft, phạm vi state theo ảnh/lượt tải, callback ổn định.
- `vercel-react-native-skills`
  - SKILL.md: `C:/Users/khatr/.agents/skills/vercel-react-native-skills/SKILL.md`
  - Why selected: Image và native media trên React Native/Expo.
  - Applied to: onLayout, URI iOS, ranh giới native image decode/display và gesture masking.

## Root cause và bằng chứng

1. **Loading có thể bị bật lại sau khi ảnh đã tải.** Trước sửa, `privacy.tsx` đặt `imageLoaded=false` và xóa lỗi ở mọi `onLoadStart`, trong khi chỉ `onLoad` mới đặt lại true. Với thứ tự `onLoad → onLoadStart`, ảnh vẫn nhìn thấy nhưng overlay trở lại vĩnh viễn nếu không còn callback success tiếp theo. Test `keeps cached iOS success terminal when loadStart arrives later or layout changes` FAIL trên màn hình trước sửa và PASS sau sửa.

   Đối chiếu mã RN đang cài:
   - `node_modules/react-native/React/Fabric/Mounting/ComponentViews/Image/RCTImageComponentView.mm`, `updateState` gọi `_setStateAndResubscribeImageResponseObserver` **trước** `onLoadStart`; `didReceiveImage` phát `onLoad` và `onLoadEnd`.
   - `node_modules/react-native/ReactCommon/react/renderer/imagemanager/ImageResponseObserverCoordinator.cpp`, nhánh `Completed` của `addObserver` trả ảnh ngay bằng `didReceiveImage`.
   - `node_modules/react-native/React/Fabric/RCTImageResponseObserverProxy.mm` chuyển callback bằng `RCTExecuteOnMainQueue`, cho phép thực thi ngay khi đang ở main thread.
   - `Image.getSize` là đường lấy kích thước/đọc ảnh riêng, có thể làm nóng cache; nó không chứng minh View Image đã render hoặc người dùng đã xác nhận privacy.
   - `ImageShadowNode.cpp` dùng kích thước layout để chọn nguồn; **bản `ImageSource::operator==` đang cài chỉ so sánh type và URI**, nên không kết luận rằng đổi layout riêng lẻ luôn tạo request mới. Test xoay/đổi layout kiểm tra không có loading loop và vẫn fit theo kích thước ảnh nguồn.

2. **JPEG chuẩn hóa bị bỏ đi.** Camera ghi lại năm field URI bằng `photo.uri`; gallery custom và gallery fallback làm tương tự với URI gốc. Store ưu tiên `originalImageUri` rồi ép `originalUri`/`sourceImageUri` về cùng giá trị. Vì vậy `NORMALIZED` có thể ghi tên JPEG mới còn `PRIVACY_INPUT` lại dùng ảnh camera/Photos gốc. Metadata JPEG/kích thước sau chuẩn hóa cũng có thể không khớp HEIC/EXIF gốc. Ba regression tests camera/custom-gallery/fallback-gallery đều FAIL trên mã trước sửa: actual URI gốc khác expected JPEG. Xem `privacy-ios-image-loading-20261026/baseline.log` và `baseline-tests.json`.

3. **Fail-open và thiếu kiểm tra file.** Pipeline trước sửa bắt lỗi manipulateAsync rồi trả URI gốc, gắn MIME JPEG dù chưa chuyển đổi/đọc thành công. Việc file tồn tại và giải mã được chưa được kiểm tra trước navigation. Privacy không có giới hạn thất bại khi native không phản hồi; callback tải ảnh cũng không được ràng buộc với từng ảnh, lần retry và focus.

**Giới hạn bằng chứng:** Không có log iPhone thật được cung cấp trong phiên này. Log mới `ios-event-sequence.log` là log từ Jest mô phỏng thứ tự callback, KHÔNG phải telemetry thiết bị. Bốn lỗi trước/sau được tái hiện bằng component tests với native modules mock; cơ chế thứ tự sự kiện được đối chiếu với mã native đã cài, chưa có trace trên iPhone xác nhận thứ tự thực tế của lần lỗi người dùng gặp.

## Thay đổi thực hiện

- `apps/student-mobile/src/app/camera.tsx`: giữ nguyên draft JPEG đã chuẩn hóa, không gán URI raw trở lại; cơ chế chống kết quả trễ/nhấn lặp hiện có được giữ.
- `apps/student-mobile/src/app/gallery.tsx`: cả hai nhánh dùng JPEG chuẩn hóa; khóa nhấn lặp; hủy hiệu lực kết quả khi blur, đổi ảnh hoặc bắt đầu lượt mới; hiển thị thông báo khi fallback không mở được ảnh.
- `apps/student-mobile/src/features/recognition/image/imagePipeline.ts`: bảo toàn `ph://`, `assets-library://`, khoảng trắng và đường dẫn percent-encoded; phải materialize JPEG thành công, output native phải là `file://`. `rawUri` chỉ giữ nguồn acquisition. Kiểm tra `getInfoAsync` và `Image.getSize` thực tế; không dùng kích thước picker để giả định ảnh hợp lệ; không fallback về ảnh gốc khi conversion lỗi. Kiểm tra đọc ảnh giới hạn 10 giây, hết hạn là lỗi.
- `apps/student-mobile/src/features/recognition/image/usePrivacyImage.ts` (mới): mỗi focus/retry có token riêng; chỉ hiển thị Image sau khi kiểm tra file/decoder; chỉ `onLoad` của attempt hiện tại mới sẵn sàng. `onLoadStart` chỉ ghi diagnostic, không reset success/error. Deadline 15 giây chuyển sang lỗi, callback đến muộn không thể phục hồi; retry tạo lượt mới và kiểm tra lại file. `onLoadEnd` không được dùng để suy ra thành công.
- `apps/student-mobile/src/features/recognition/state/recognitionDraftStore.ts`: bổ sung subscribe/getSnapshot cho privacy theo dõi thay ảnh; giữ alias nguồn chuẩn hóa riêng khỏi ảnh đã che/crop. `rawUri` không được dùng làm đường phục hồi ngầm khi ảnh mất.
- `apps/student-mobile/src/app/privacy.tsx`: editor remount theo session/URI; confirmation thuộc từng attempt, masks giữ khi retry cùng ảnh. Tiếp tục chỉ khi có native load success, layout dương và xác nhận người dùng. Kiểm tra lại nguồn trước xử lý; ảnh ViewShot cũng phải đọc được trước khi lưu draft. Kết quả sau blur/unmount bị bỏ qua. Giữ nguyên vẽ/di chuyển/đổi cỡ/xóa/hoàn tác vùng che và flow privacy → crop; không gọi upload tại privacy.

Tests sửa/bổ sung:
- `src/__tests__/privacyScreen.test.tsx`
- `src/__tests__/cameraCompanion.test.tsx`
- `src/__tests__/galleryImageLifecycle.test.tsx` (mới)
- `src/features/recognition/image/__tests__/imagePipeline.test.ts`

Không sửa backend, Groq, Gemini, model AI, dependency hay cấu hình môi trường. Không reset/commit/push/deploy. Các WIP có sẵn được giữ. Kiểm chứng baseline dùng bản HEAD của đúng ba file màn hình, có backup và phục hồi byte-for-byte, không dùng git reset/checkout.

## Kết quả kiểm tra

| Kiểm tra | Kết quả |
| --- | --- |
| Bốn ca lỗi trên mã màn hình trước sửa | EXPECTED FAIL: 4/4 |
| Nhóm privacy/camera/gallery/pipeline | PASS: 62/62 tests, 5 suites |
| Toàn bộ Jest student-mobile | PASS: 981 passed, 0 failed, 0 skipped; 82/82 suites passed |
| TypeScript (`npm run typecheck`) | PASS; `typecheck.log` |
| Lint (`npm run lint`) | PASS, 0 errors; hai warning có sẵn ở `cropRotation.web.ts:12,39`; `lint.log` |
| Bundle iOS (`npx expo export --platform ios`) | PASS, Hermes bundle 6.5 MB và assets; `ios-export.log` |
| Node multi-mask gesture audit/simulation | PASS (1 test file); native gestures vẫn cần iPhone |
| `git diff --check` | PASS; có cảnh báo LF/CRLF của WIP có sẵn |
| iPhone / native gestures / Photos thật / iCloud | CHƯA CHẠY trên thiết bị vật lý |

Logs/JSON ở `report/privacy-ios-image-loading-20261026/`. Bundle export nằm tại `C:/Users/khatr/mathvision-privacy-ios-20261026/`; đây là bundle JavaScript/assets, không phải IPA/native build hay bằng chứng đã chạy trên iPhone. Máy làm việc Windows không có Xcode/iOS Simulator. Manifest hiện tại dùng Expo 58, RN 0.88; không thay SDK.

Các ca bao phủ: success → late start; getSize không thay native load; load error; decode error; file mất/rỗng/thư mục; kích thước decoder không hợp lệ; file lookup treo và callback muộn; native không phát success; retry đọc lại file; ảnh mới không nhận confirmation/mask cũ; blur/refocus; camera/gallery trả kết quả trễ; picker cancel; nhấn lặp; mask giữ qua retry và xuất đúng rasterized URI. Bộ tests cũ còn kiểm tra mask geometry, gesture architecture và privacy/upload boundary.

Tests còn thất bại: không có. Lượt thu log callback riêng đầu tiên timeout ở ngưỡng Jest 5 giây khi chạy đồng thời với export/typecheck; chạy lại riêng PASS, không đổi runtime code hoặc nâng timeout. Bộ đầy đủ 981 tests đã PASS với timeout mặc định. Trong quá trình phát triển cũng đã sửa mock `onLayout` khi remount và async `act` chưa được chờ trong test camera cũ.

## Xác nhận trên iPhone thật

1. Mở terminal trong `C:/MathVisonKid/apps/student-mobile`, chạy `npx expo start --lan --clear`. iPhone và máy tính cùng mạng, mở dự án bằng QR trong Expo Go tương thích SDK của dự án. Giữ cấu hình/backend hiện có để kiểm tra luồng sau crop.
2. Chụp trang có tên giả. Privacy phải hiện ảnh đúng chiều và mất overlay sau khi ảnh mở; không cho tiếp tục khi chưa tick xác nhận. Che tên, di chuyển, đổi cỡ, xóa một vùng, hoàn tác rồi che lại; tick xác nhận và tiếp tục. Ảnh ở crop/preview phải giữ vùng che.
3. Quay lại privacy, xoay ngang/dọc, rời màn hình rồi quay lại. Ảnh phải fit đủ trang, vùng che đúng vị trí; không loading loop. Xác nhận lại nếu bắt đầu lượt focus mới.
4. Lặp lại với ảnh HEIC từ Photos, ảnh chân dung/ngang, ảnh từ bộ chọn thư viện ở camera; nếu dùng custom gallery thì thử cả nhánh đó. Thử chọn ảnh khác nhanh, hủy picker, rời màn hình trong lúc nhận ảnh rồi quay lại: kết quả cũ không được thay ảnh mới hoặc tự mở privacy.
5. Khi gặp ảnh không mở được, phải có thông báo và “Thử tải lại ảnh”, không spinner vô hạn. Retry vẫn không cho tiếp tục nếu file không đọc được; chọn/chụp lại ảnh mới. Mất cache, decoder treo và native không phát callback đã được mô phỏng trong tests, chưa tạo lỗi file sandbox thật trên iPhone.
6. Đối chiếu log developer: filename ở `[DEV_STAGE][NORMALIZED]` và `[DEV_STAGE][PRIVACY_INPUT]` phải trùng JPEG đã chuẩn hóa; khác filename acquisition là bình thường. `IMAGE_READABLE` có kích thước dương; `PRIVACY_LOAD_SUCCESS` làm overlay biến mất. Nếu `PRIVACY_LOAD_START` đến sau success, status phải vẫn `ready`; lỗi có `IMAGE_READ_ERROR` hoặc `PRIVACY_LOAD_ERROR`. Không cần đưa URI đầy đủ hoặc ảnh chứa thông tin cá nhân vào báo cáo.

Chưa xác nhận trực tiếp: native event order trên Expo Go/iPhone đang dùng, quyền Photos limited, ảnh iCloud chưa tải, sandbox URI thật, EXIF của ảnh thật, độ chính xác mask sau xoay trên thiết bị và end-to-end upload ảnh đã che trên iPhone.

## Tài liệu đối chiếu

- [React Native Image: getSize và các load events](https://reactnative.dev/docs/image)
- [Expo SDK 57 ImageManipulator (tài liệu version bắt buộc của AGENTS.md)](https://docs.expo.dev/versions/v57.0.0/sdk/imagemanipulator/)
- [Expo SDK 57 FileSystem legacy](https://docs.expo.dev/versions/v57.0.0/sdk/filesystem-legacy/)
- Hành vi thực tế được đối chiếu thêm với source RN/Expo đang cài, thay vì giả định SDK 57 trùng SDK 58.
