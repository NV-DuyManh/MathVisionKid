# Dữ liệu đánh giá bộ kiểm chứng

`tests/fixtures/validator_knowledge_cases.json` là bộ ca tổng hợp có đáp án được tính rõ ràng để kiểm tra **căn cứ số học cục bộ**, không phải dữ liệu đã train model và không phải tập nghiên cứu độc lập chưa từng xem.

Mỗi ca gồm: `id`, `family`, `source`, `expression`, `answer` chính xác, `unit`, `accept`. `accept=false` có thể là phép tính sai hệ số, hoặc có kết quả cuối đúng nhưng dùng số/đáp án chưa được chứng minh. Nó không có nghĩa mọi ca âm đều cho kết quả số sai.

Chạy từ `ai/runtime`:

```powershell
./.venv/Scripts/python.exe scripts/benchmark_lesson_validator.py --output ../../.local-artifacts/validator-knowledge/result.json --log ../../infra/local-runtime/logs/fastapi.err.log
```

Quy ước:

- Chỉ thêm ca đã kiểm tra dữ kiện, phép tính, đơn vị và kết quả. Mỗi lỗi chặn nhầm cần có ca đúng và một ca sai gần giống để tránh nới lỏng quá mức.
- Không lấy kết quả được model đồng ý làm nhãn chuẩn tự động. Một lần retry thành công chưa chứng minh lần từ chối trước là sai.
- Không sao chép tên/tài khoản/ảnh riêng của học sinh vào repo. Nhật ký mới chỉ lưu mã lỗi, dấu vân tay nguồn và các cờ kiểm tra; chưa đủ để làm tập train có nhãn chuẩn.
- Đánh giá ngữ nghĩa/model phải có tập bài và nhãn riêng. Không công bố tỷ lệ lỗi của bộ ca này là độ chính xác OCR/model hoặc bằng chứng không bao giờ lỗi.
- Khi thực sự tinh chỉnh model riêng, tách dữ liệu theo nguồn/dạng bài trước khi train; giữ tập đánh giá riêng, không chia ngẫu nhiên các bản đổi số của cùng một bài sang cả hai phía.

Hệ số SI/thời gian/héc-ta/lít/tấn tham khảo [NIST SP 330, mục 4](https://www.nist.gov/pml/special-publication-330/sp-330-section-4) và [BIPM SI Brochure](https://www.bipm.org/en/publications/si-brochure). Tạ/yến và cách viết tiếng Việt được khai báo rõ trong `math_knowledge.py`; không tải kiến thức từ model vào bảng quy tắc tự động.
