# FaceTracing

Prototype CV và procedural animation cho AI-assisted Protogen helmet dùng trong cosplay. Người đội quyết định tương tác thực tế; hệ thống hỗ trợ animation từ các event thị giác.

Hiện project có laptop runner để kiểm chứng face detection, filtering và renderer của Raspieyes trên CPU. Attention Engine, interaction lock và RoboEyes integration nằm trong các milestone tiếp theo.

## Bắt đầu

- [Cài đặt và chạy thử](experiments/README.md): tải Raspieyes tại commit cố định, áp dụng patch, tạo Python environment rồi chạy mouse/webcam/benchmark.
- [Roadmap và checkpoint](ROADMAP.md): mục tiêu, phạm vi và bằng chứng cần có cho từng milestone.
- [Cấu hình](experiments/config.json): detector, camera index, FPS, warm-up và thời gian đo.

Sau khi hoàn thành cài đặt, chạy từ root project:

```bash
raspieyes/.venv/bin/python experiments/run_raspieyes.py --mode mouse
raspieyes/.venv/bin/python experiments/run_raspieyes.py --mode webcam
raspieyes/.venv/bin/python experiments/run_raspieyes.py --mode benchmark
```

## Dependency và kết quả local

[Raspieyes](https://github.com/alevizio/raspieyes) được clone riêng vào `raspieyes/`, ngoài các file được track bởi repo chính. [Patch benchmark hooks](patches/raspieyes-benchmark-hooks.patch) giữ các thay đổi cần cho runner. Khi chỉnh source của dependency, cập nhật patch theo hướng dẫn cài đặt trước khi commit.

JSON kết quả nằm trong `benchmark/` và bị ignore cùng Python environment/cache. Các link tới kết quả local trong tài liệu chỉ hoạt động trên máy đã tạo hoặc nhận các file đó. Số liệu laptop chưa xác nhận hiệu năng, nhiệt hoặc công suất trên Raspberry Pi 5.

## Kiểm tra kỹ thuật

```bash
raspieyes/.venv/bin/python -m unittest discover -s experiments/tests -v
```

Integration checks dùng video giả lập và headless rendering; không mở webcam thật.
