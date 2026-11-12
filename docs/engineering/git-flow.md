# Git Flow của MathVisionKid

Áp dụng từ 2026-11-12, theo tài liệu Git Flow Rule do owner cung cấp. `develop` là nhánh mặc định khi clone và nơi tích hợp; `main` là code đã chốt phiên bản. Đây là quy trình nguồn, không đồng nghĩa đã triển khai AppStore/TestFlight hay production.

## Nhánh và đích PR

| Nhánh | Tách từ | Đích PR |
| --- | --- | --- |
| `feature/<task>` | develop mới nhất | develop |
| `bugfix/<task>` | develop mới nhất | develop |
| `release/<major.minor.patch>` | develop sau khi scope ổn định | main, sau đó develop |
| `hotfix/<major.minor.patch>_<task>` | main hoặc tag đã phát hành | main, sau đó develop |
| `bugfix/<task>` để ổn định release/hotfix | đúng release/hotfix cần sửa | nhánh release/hotfix đó |
| `main` để đồng bộ commit merge cuối | main | develop |
| `dependabot/*` do dependabot[bot] tạo | develop | develop |

Tên task viết thường, dùng gạch ngang; có thể dùng `feature/#123_short-description`. Không bịa issue ID. Không tạo release mới cho từng task: hoàn thành feature qua PR về develop trước, chỉ tách release khi cả phiên bản đã ổn định. Quy tắc này làm rõ đoạn “khi xong feature” dễ hiểu nhầm trong tài liệu nguồn. Bugfix vẫn được phép vào develop dù bảng nguồn “develop chỉ nhận” bỏ sót loại nhánh này.

## Làm một task

```powershell
git fetch origin
git switch develop
git merge --ff-only origin/develop
git switch -c feature/short-description
# Sửa, tự đọc diff, dùng AI review, chạy kiểm tra phù hợp, commit rõ mục đích.
git push -u origin feature/short-description
gh pr create --base develop
```

Commit và tiêu đề PR dùng Conventional Commits (`feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`...). Trước review/merge, merge develop mới nhất vào task nếu cần; không rebase rồi force-push nhánh chung. CI kiểm tra chính PR head có chứa base mới nhất, thay vì chỉ kiểm tra merge commit tổng hợp của GitHub.

PR ghi nguồn yêu cầu thật, trước/sau, kiểm thử và bằng chứng đã lọc dữ liệu, rủi ro, cấu hình/migration và việc phải làm sau merge. Gán assignee/reviewer thực tế. Người review xem kết quả bot, AI review và CI trước khi Approve; ít nhất một người khác Approve. Owner `NV-DuyManh` được miễn bước approval theo yêu cầu riêng, vẫn cần PR, đúng luồng, Quality gate đạt, không còn discussion chưa xử lý. Không tự Approve hoặc tự resolve bình luận của người khác.

Bot trong CI kiểm tra policy, dữ liệu riêng tư, workflow an toàn và chọn test. Bot không phải mô hình AI review ngữ nghĩa; AI review được agent/người thực hiện ghi kết quả và revision trong PR. Không tuyên bố có dịch vụ AI review tự động khi chưa cấu hình dịch vụ đó.

## Chốt phiên bản và hotfix

1. Merge task đã review vào develop. Chạy lại luồng chính, chốt scope rồi tách `release/1.0.1` từ develop. Với lỗi production, tách `hotfix/1.0.2_fix-description` từ main/tag.
2. Release/hotfix chỉ nhận sửa lỗi, nội dung, version, metadata và test; không thêm tính năng. Nếu cần sửa, dùng bugfix PR vào đúng nhánh ổn định. CI chặn PR/commit `feat` trong bước này; reviewer phải kiểm tra nội dung thực tế.
3. Thêm `docs/releases/<version>.md` ghi thay đổi, kiểm thử, ảnh hưởng và rollback. Mở PR vào main, kiểm tra xung đột, chờ bot/CI và approval theo quyền. Main/release/hotfix dùng merge commit để giữ ancestry cho backmerge; không squash/rebase các nhánh này.
4. Sau main merge và Quality gate của push main đạt, CI tạo GitHub source release và tag bất biến `v<version>_prod` đúng merge SHA. Không di chuyển tag đã công bố. Đây là source release sẵn sàng triển khai, không phải chứng cứ đã deploy production/AppStore.
5. Mở PR nhánh release/hotfix về develop rồi PR main về develop nếu còn thiếu merge commit. Giải quyết xung đột trên nhánh riêng, giữ cả thay đổi develop mới và bản sửa đã phát hành. Không xóa release/hotfix trước bước này.
6. Khi có triển khai TestFlight thực tế, tag `v<version>_stg` phải trỏ đúng revision đã kiểm thử. Không tự tạo tag staging chỉ vì CI xanh. Chỉ triển khai store/production khi được owner cho phép riêng.

Dependabot dùng develop cho cả cập nhật thường và security vì develop là default branch. Nếu lỗ hổng ảnh hưởng bản production, tách hotfix từ main để vá ngay rồi backmerge, không đợi release kế tiếp.

## Bắt buộc trên GitHub

`main`, `develop`, `release/*`, `hotfix/*` yêu cầu PR và Quality gate đúng GitHub Actions app, xử lý discussion và chặn force-push. Main/develop còn chặn xóa nhánh. Một ruleset riêng yêu cầu 1 approval, chỉ user ID 154242112 của owner được bypass ở chế độ pull_request; không có bypass cho CI/history. File `.github/rulesets/*.json` là cấu hình đích, phải kiểm tra trạng thái live như hướng dẫn [GitHub settings](github-settings.md).

CI kiểm tra đích PR, loại nhánh, revision task đã cập nhật, release notes và không thêm feat lúc ổn định. Kiểm tra tên/commit không chứng minh nội dung tính năng hay lịch sử tách nhánh ban đầu; reviewer kiểm tra diff/ancestry và nguồn yêu cầu. Không sửa policy để né lỗi. Cùng một người không thể vừa tạo PR vừa tính là approval cho mình.

## Chuyển tiếp và rollback

Đợt chuyển đổi bắt đầu từ main `48c1c7a95966391842a05c80794298207d05cc55`: tạo develop cùng revision, đưa feature policy vào develop rồi release vào main và backmerge. Không viết lại lịch sử cũ. PR #51 giữ nguyên tác giả/head và chuyển base develop; CI chỉ nhận ngoại lệ đúng số PR, head, repository, ngày tạo tới 2026-11-26. Nếu hết hạn, người làm đưa commit qua feature branch hợp lệ, giữ attribution. Những nhánh cũ khác không tự được miễn.

Snapshot rulesets/settings cũ lưu ngoài Git trong `.local-artifacts/git-flow-migration/`. Nếu có lỗi, sửa qua bugfix/hotfix và PR; không tắt Quality gate/force-push hoặc tự bypass. Khôi phục cấu hình server từ snapshot chỉ khi owner yêu cầu rõ ràng.
