## Vấn đề và kết quả

Nguồn yêu cầu / issue thật:

Git Flow: head → base, nguồn tách nhánh, release/hotfix cần backmerge vào develop:

Assignee / reviewer thực tế:

Hành vi trước → sau:

## Kiểm tra

- Lệnh / tình huống và kết quả:
- Ảnh UI đã lọc dữ liệu riêng tư, nếu thay giao diện:
- Chưa kiểm tra và lý do:

## AI review

- Revision đã review, agent/người thực hiện, findings và cách xử lý:
- Người review đọc kết quả bot/CI trước khi Approve; không tự resolve bình luận của người khác.

## Tác động và phát hành

- API / migration / cấu hình / dependency:
- Rủi ro và cách rollback:
- Nguồn code / tác giả gốc nếu tích hợp:
- Skills áp dụng, đường dẫn SKILL.md và phạm vi:

## Trước khi merge

- [ ] Đạt tiêu chí nghiệm thu; required checks đạt
- [ ] Đúng đích Git Flow; đã xử lý blockers/discussions; có 1 approval từ người khác (owner `NV-DuyManh` được miễn approval)
- [ ] Nếu vào main: có release notes đúng version; giữ release/hotfix tới khi backmerge develop
- [ ] Không có secret, ảnh học sinh hoặc dữ liệu nghiên cứu riêng tư
- [ ] Không bỏ kiểm chứng toán / backend RBAC để làm xanh giao diện
- [ ] Ghi đúng giới hạn kiểm thử, không coi mock là bằng chứng thiết bị thật
