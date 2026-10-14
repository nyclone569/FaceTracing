# Roadmap — AI-assisted Protogen Helmet

Ngày tạo: 2026-10-13

Trạng thái cập nhật 2026-10-14: công cụ kiểm chứng laptop và public GitHub branch đã có; M0–M1 đang thực hiện, M2 có phần chuẩn bị dữ liệu. Chưa có milestone M0–M8 nào đạt toàn bộ điều kiện hoàn thành. Phiên benchmark webcam hiện mới có lượt 5 FPS.

Phạm vi hiện tại: kiểm chứng tính khả thi và độ ổn định của luồng model trên **webcam laptop, CPU local** trước khi mua thiết bị. Raspberry Pi/camera của helmet và phép đo trên thiết bị đích defer đến M8. Video ghi sẵn, annotation chính thức và chia tập tuning/evaluation sẽ bổ sung sau; không chặn thử nghiệm webcam ban đầu.

Cập nhật 2026-10-14: đã thêm laptop runner cho bước 5–6 tại [experiments/run_raspieyes.py](experiments/run_raspieyes.py), cấu hình và JSON metrics. Xem [hướng dẫn và điểm nối RoboEyes](experiments/README.md). Đây là công cụ kiểm chứng baseline; milestone chỉ được đánh dấu khi có đủ bằng chứng theo tiêu chí bên dưới.

Quyết định quản lý source: `raspieyes/` được ignore trong repo chính, tải riêng tại upstream commit cố định rồi áp dụng [patch benchmark hooks](patches/raspieyes-benchmark-hooks.patch). [Hướng dẫn cài đặt](experiments/README.md) mô tả cách tái tạo source trên máy mới. Các kết quả trong `benchmark/` là dữ liệu local, chưa được commit.

## Cách sử dụng

- `[ ]`: chưa hoàn thành; `[x]`: đã hoàn thành và có bằng chứng kiểm chứng.
- Checklist gộp được tách khi mới hoàn thành một phần, để phân biệt smoke test, chạy thực tế và đánh giá chất lượng.
- Chỉ đánh dấu milestone khi đạt các điều kiện hoàn thành của milestone đó.
- Ghi cấu hình, kết quả, hạn chế và quyết định vào phần nhật ký cuối tài liệu.
- Các tần số và ngưỡng trong roadmap là mục tiêu thử nghiệm, chưa phải hiệu năng đã đo.
- Roadmap không tự cấp phép triển khai code, mua phần cứng hoặc mở rộng scope. Bắt đầu triển khai khi người dùng yêu cầu.

## Mục tiêu và quyết định đã thống nhất

Helmet dùng cho cosplay. Người đội quyết định hành động và tương tác thực tế; AI hỗ trợ điều chỉnh animation theo event bên ngoài để giảm điều khiển biểu cảm thủ công.

Pipeline MVP:

```text
Camera → CV → Face Tracking → Attention Engine
       → Character State Machine → Animation Intent → RoboEyes Adapter → Renderer
```

- Laptop 32 GB RAM, CPU local là môi trường thử nghiệm chính. FPS thực tế còn phụ thuộc CPU, camera, model và cấu hình.
- Colab là công cụ bổ trợ cho thử nghiệm offline trên ảnh/video hoặc model cần GPU; không dùng làm benchmark realtime chính.
- Face tracking điều khiển mắt helmet nhìn theo người. Head orientation là attention proxy; eye-gaze estimation là nhánh kiểm chứng tùy chọn.
- `OBSERVE`: utility scoring + hysteresis chọn target quan sát.
- `INTERACT`: interaction lock ưu tiên giữ target hơn scoring thông thường.
- RoboEyes cung cấp animation primitives; Character State Machine điều phối event, timing và hành vi.
- Animation chạy độc lập với inference; hướng mắt và biểu cảm được cập nhật liên tục.
- Dùng tham số và randomness có kiểm soát cho biến thể hành vi ban đầu.
- Defer LLM/VLM đến sau MVP. Không mở rộng sang audio, speech recognition hoặc conversational AI.
- Chuyển động đầu của người đội, camera motion và IMU được xử lý ở milestone sau baseline.

## Giới hạn diễn giải perception

| Observation / ước lượng | Có thể sử dụng cho | Không đủ để kết luận |
|---|---|---|
| Vị trí và lịch sử face track | Hướng mắt, chuyển động tương đối trong ảnh | Danh tính của người |
| Khuôn mặt lớn dần | Một dấu hiệu trong approaching estimate | Người chắc chắn đang tiến lại gần |
| Head orientation hướng camera | Attention proxy | Eye gaze hoặc ý định trò chuyện |
| `passing`, `approaching`, `interaction_candidate` | Event có confidence để điều phối animation | Hành vi hoặc ý định đã được xác nhận |
| Interaction lock | Giữ target theo chính sách của helmet | Người đó chắc chắn đang nói chuyện với người đội |
| Không tìm thấy face | Chưa có face observation đáng tin cậy | Camera vẫn hoạt động tốt hoặc không có người |

## Tổng quan milestone

| Hoàn thành | Milestone | Hiện trạng / phần còn thiếu | Phụ thuộc |
|---|---|---|---|
| [ ] | M0 — Protocol và baseline | Có metadata, pinned Raspieyes/model và RoboEyes stable, hướng dẫn và phương pháp đo; cần ghi điều kiện webcam trực tiếp/kiểm tra license. Video và thiết bị helmet defer | — |
| [ ] | M1 — Model trên laptop CPU | Toàn bộ checkpoint M1 kiểm chứng trên laptop. Có MediaPipe webcam, smoke test DNN và JSON metrics; thiếu DNN live, Face Landmarker, các lượt đủ thời lượng và điều tra CPU cao | M0 |
| [ ] | M2 — Tracking và độ tin cậy | Đã kiểm tra detection → EMA/dead zone → target và schema log; chưa có track ID, freshness policy và kiểm chứng mất dấu/camera failure đầy đủ | M1 |
| [ ] | M3 — Attention cues | Chưa triển khai head pose, attention proxy hoặc event từ track history | M2 |
| [ ] | M4 — RoboEyes và Character State Machine | Có seam TargetSnapshot/AnimationIntent và Raspieyes backend; chưa có RoboEyes adapter hoặc Character State Machine | M2; dùng cues M3 khi sẵn sàng |
| [ ] | M5 — Interaction lock | Chưa triển khai scoring, observe/interact hoặc acquire/hold/release policy | M3, M4 |
| [ ] | M6 — Nhiều người và attention competition | Chưa kiểm chứng association, target competition hoặc interaction lock nhiều người | M5 |
| [ ] | M7 — Môi trường và degraded behavior | Có xử lý lỗi/signal ở runner; chưa kiểm chứng các tình huống môi trường và recovery của character | M6 |
| [ ] | M8 — Raspberry Pi 5 và quyết định camera | Chưa benchmark trên Pi; camera/accelerator chưa chốt | M7; phần cứng được phép sử dụng |

M0–M5 tạo baseline hành vi trên laptop. M6–M7 tăng độ phức tạp và kiểm chứng tính ổn định. M8 xác nhận khả năng chạy trên thiết bị đích.

## Công cụ và quản lý project — đã hoàn thành

- [x] Tạo [runner Python](experiments/run_raspieyes.py) cho mouse, webcam và benchmark 5/10/15 FPS; có config riêng.
- [x] Ghi JSON gồm metadata, detector thực tế, stage timings, completed FPS, process CPU/RSS và target samples; có checkpoint và lưu khi dừng.
- [x] Tách [TargetSnapshot → AnimationIntent → RaspieyesBackend](experiments/raspieyes_adapter.py) để thấy điểm nối perception/animation; chưa thay bằng RoboEyes.
- [x] Tạo 8 kiểm tra kỹ thuật cho thống kê, JSON, render headless, DNN/MediaPipe trên video giả lập, lỗi nguồn và signal shutdown.
- [x] Kiểm chứng cài lại từ upstream checkout sạch + patch; 8 tests pass ở cấu trúc tái tạo này.
- [x] Ignore dependency local `raspieyes/`, Python environment/cache và dữ liệu `benchmark/` trong repo cha.
- [x] Lưu [patch benchmark hooks](patches/raspieyes-benchmark-hooks.patch) và [hướng dẫn clone/apply/install](experiments/README.md).
- [x] Commit và push baseline lên [public branch feat/laptop-benchmark](https://github.com/nyclone569/FaceTracing/tree/feat/laptop-benchmark), commit [1bf2fa0](https://github.com/nyclone569/FaceTracing/commit/1bf2fa01ff9a93719b67e3db45cfcd12626f4054).

Các checkpoint công cụ không thay thế tiêu chí chất lượng, scenario coverage và hiệu năng của M0–M8.

## M0 — Chuẩn bị protocol và baseline

- [x] Ghi CPU, OS, logical CPU count, Python và package versions trong JSON; ghi camera index/backend, format và FPS do driver báo. Máy baseline: Core 7 240H, 16 logical CPUs, Ubuntu 24.04, Python 3.12.
- [ ] Ghi điều kiện laptop khi thử: camera đang dùng, ánh sáng, tải nền và chế độ nguồn nếu biết. Chọn phần cứng helmet/Raspberry Pi không thuộc điều kiện hoàn thành M0 hiện tại.
- [x] Chốt Raspieyes commit `6289af4d6430dcf1107fce94907fa3ee1fd52d7f`, MediaPipe 0.10.21 và model assets cho thử nghiệm hiện tại; JSON có checksums, repo giữ patch.
- [x] Chọn RoboEyes stable mới nhất đã kiểm tra ngày 2026-10-14: [v1.1.2](https://github.com/FluxGarage/RoboEyes/releases/tag/v1.1.2), commit `a35185d24cc8a50ee4c8b1e558cd5d85e880e2b3`. Pin tag/commit này cho baseline M4; chưa kiểm chứng desktop adapter.
- [ ] Kiểm tra license của code, dependencies và model trước khi chốt phương án tái sử dụng.
- [x] Phân biệt component thực sự được dùng: detection chọn một face, double EMA/dead zone, TrackingState và renderer; centroid/Kalman không chạy trong detection loop hiện tại. RoboEyes/Attention/FSM vẫn là bước sau.
- [x] Ghi capture resolution, driver-reported FPS và detection/render target/actual FPS trong benchmark JSON.
- [ ] Ghi khoảng cách xấp xỉ và ánh sáng bằng `test_context` trong config hoặc ghi chú của phiên thử; `face_width` không phải khoảng cách vật lý đã đo.
- [ ] Thực hiện cùng trình tự tình huống trực tiếp trên webcam: không người, một người đứng yên, di chuyển/quay mặt nhẹ, rồi rời khung hình; ghi quan sát về detection, jitter và lag.
- [x] Định nghĩa và triển khai cách đo process CPU/RSS, stage latency, completed result FPS và tuổi frame tại host; [tài liệu metrics](experiments/README.md) ghi rõ giới hạn camera buffering, native worker CPU và reaction latency.

**Điều kiện hoàn thành hiện tại:** có protocol webcam đơn giản có thể lặp lại, môi trường/model được ghi rõ và hiểu giới hạn phép đo. Không yêu cầu đã mua Pi/camera hoặc có video ghi sẵn.

Defer và giữ lại để bổ sung sau baseline webcam:

- [ ] Chuẩn bị video không người, một người, walk-by, nhìn camera, quay mặt, tiếp cận và rời đi.
- [ ] Gán nhãn mốc event để đo reaction latency/accuracy chính thức.
- [ ] Tách tập dùng chỉnh tham số khỏi tập dùng đánh giá khi đã có bộ video.

Các hạng mục defer không tính là đã hoàn thành và không chặn M1 kiểm chứng model trên webcam hiện tại.

## M1 — Kiểm chứng model trên laptop CPU

**Tất cả checkpoint ở M1 chạy được trên laptop hiện tại.** M1 xác nhận model/pipeline có thể hoạt động trên CPU, đánh giá output và workload ban đầu. Hiệu năng, RAM, nhiệt/công suất trên Pi, chất lượng Camera Module 3/IMX500 và nhu cầu accelerator chỉ được xác nhận ở M8.

- [x] Chạy baseline MediaPipe Face Detector / BlazeFace từ Raspieyes. Bằng chứng: webcam 10 FPS và benchmark 5 FPS ngày 2026-10-14, camera 0, ảnh thực tế 640×480; các phiên dừng chủ động.
- [x] Smoke-test OpenCV DNN và MediaPipe trên video giả lập không có face; kiểm tra DNN ở 5/10/15 FPS và chế độ perception-only bằng integration tests.
- [ ] Chạy OpenCV DNN trên cùng webcam laptop với MediaPipe, cùng config/điều kiện/trình tự thao tác; đổi backend bằng `--detector dnn`. Đối chứng bằng video giống hệt nhau sẽ bổ sung khi có dữ liệu.
- [x] Ghi detector thực sự hoạt động, kể cả khi fallback; không gộp kết quả khác detector. Các phiên webcam/benchmark hiện tại ghi `actual_detector=mediapipe`, motion fallback tắt.
- [ ] Đo `webcam → Face Landmarker (num_faces=1) → landmarks` độc lập. Task đã có detector bên trong; đo tổng chi phí detection + landmarks trước khi quyết định có cần detector ngoài. Runner hiện chưa có Face Landmarker backend.
- [x] Chạy thử MediaPipe webcam ở detection target 5 và 10 FPS, capture thực tế 640×480; driver báo 30 FPS. Renderer giữ khoảng 30 FPS trong các phiên ngắn.
- [ ] Chạy đủ thời lượng các lượt webcam 10/15 FPS tiếp theo; `benchmark_rates` mặc định hiện là `[10, 15]`. Có thể đo lại đủ 5/10/15 bằng `--rates 5 10 15` để so sánh nhất quán; phiên 5 FPS cũ chỉ là chạy thử ngắn.
- [ ] Đo perception-only: camera + preprocessing + detector + filtering + metrics, tắt animation/render bằng `--perception-only`; đối chiếu phiên có renderer cùng detector/rate/config trên laptop.
- [x] Ghi P50/P95/P99 capture/preprocessing/detection-stage/host-frame-to-target/render latency, completed FPS, process CPU và sampled RSS trong JSON. Warm-up/shutdown tách khỏi summary.
- [ ] Trên laptop, bổ sung phép đo/đối chứng cho CPU inference tính đủ native workers, peak RAM theo run và dropped/skipped frames; số liệu hiện tại chưa bao phủ đủ. Đây là cải thiện instrumentation/profiling, không đòi hỏi mua Pi/camera mới.
- [ ] Điều tra CPU process cao: webcam 10 FPS khoảng 1231.6%, benchmark 5 FPS khoảng 710.8% theo thang 100%=1 logical CPU; chưa xác định nguyên nhân hoặc bottleneck.
- [ ] Đánh giá miss detection, false detection, face box jitter và ảnh hưởng của mặt nhỏ/quay nghiêng.
- [ ] Chọn detector baseline dựa trên chất lượng và chi phí; ghi rõ giới hạn của model chưa chọn.

**Điều kiện hoàn thành hiện tại:** có đối chứng webcam được mô tả rõ, biết output/model ổn định đến đâu và cấu hình laptop nào có thể bước sang tracking. Chạy liên tục để kiểm tra lỗi, FPS và RAM bất thường trước khi coi baseline ổn định. Live webcam chưa bảo đảm các model nhận cùng chuỗi frame; ghi giới hạn này cho tới khi có video. Kết quả không chứng minh Pi đạt cùng FPS hoặc công suất.

## M2 — Face tracking một người và reliability tối thiểu

- [x] Kiểm tra đường dữ liệu thực tế trong Raspieyes: detection → double EMA/dead zone → TrackingState → TargetSnapshot → baseline AnimationIntent. Chưa có multi-face track ID hoặc Kalman trong nhánh này.
- [x] Chuẩn hóa observation cho logging: `capture_received_s`, `completed_s`, raw/filtered target, face width, confidence nếu detector có, backend và target source. Capture timestamp là lúc nhận ảnh tại host, không phải sensor exposure.
- [ ] Hoàn thiện observation contract dùng cho Attention Engine, gồm confidence/freshness/source và liên kết track ID; schema log hiện tại mới là nền tảng.
- [ ] Theo dõi track ID tạm thời, last-seen, position và velocity; không dùng facial identity recognition.
- [ ] Kiểm chứng filtering bằng cả jitter và độ trễ; dùng thời gian thực khi nhịp frame thay đổi.
- [ ] Chốt confidence gating, ngưỡng observation quá cũ và giới hạn prediction khi mất dấu.
- [ ] Xử lý occlusion ngắn: giữ target có giới hạn, confidence giảm theo thời gian, rồi release.
- [ ] Phân biệt no detection, frame quá cũ, capture failure và inference failure.
- [ ] Kiểm chứng camera đứng hình/ngắt kết nối: không giữ vô hạn trạng thái hoặc hướng mắt cũ.
- [ ] Kiểm tra mirror và quy ước tọa độ trước khi mapping target sang hướng mắt chuẩn hóa.
- [ ] Tránh queue frame tăng dần; ưu tiên observation mới và ghi nhận frame bị bỏ.

**Điều kiện hoàn thành:** một người được theo ổn định; mất target và camera failure có hành vi xác định; dữ liệu cũ không tiếp tục tạo phản ứng mới. Có thể dùng debug visualization đơn giản ở bước này.

## M3 — Attention proxy và event từ lịch sử track

- [ ] Kiểm chứng head orientation bằng landmarks/transformation matrix hoặc pose estimation; xác minh quy ước trục.
- [ ] Dùng nhãn `toward_camera`, `away`, `unknown` với confidence và thời gian duy trì.
- [ ] So sánh đầu/mắt cùng hướng camera, đầu hướng camera nhưng mắt lệch, đầu lệch nhưng mắt nhìn camera.
- [ ] Đánh giá kính, mặt nhỏ, quay nghiêng và ánh sáng kém; cho phép trả `unknown`.
- [ ] Thiết kế `passing`, `approaching`, `interaction_candidate` từ lịch sử track, không từ một frame đơn lẻ.
- [ ] Kiểm chứng false approaching do thay đổi pose, detector box hoặc chuyển động ngang; không dùng face size làm bằng chứng duy nhất.
- [ ] Gắn confidence, timestamp và lý do với event; tránh phát lặp một event ở mọi frame.
- [ ] Quyết định có cần thí nghiệm eye gaze hay head-pose proxy đã đủ cho baseline.
- [ ] Nếu thử eye gaze: đo lợi ích chất lượng và chi phí tăng thêm trên cùng bộ tình huống; ghi quyết định giữ/defer.

**Điều kiện hoàn thành:** biết cues nào đáng tin trong điều kiện nào; event là ước lượng có thể giải thích. Eye gaze không phải điều kiện bắt buộc để hoàn thành milestone.

## M4 — RoboEyes adapter và Character State Machine

- [ ] Kiểm chứng phương án tái sử dụng core RoboEyes trên desktop qua adapter cho graphics, clock và random.
- [ ] Chốt phương án reuse/port sau thử nghiệm tương thích; không mặc định RoboEyes cắm trực tiếp vào Python/Raspieyes.
- [ ] Định nghĩa Animation Intent: gaze target liên tục, expression, blink request, transition timing và observation freshness.
- [ ] Bổ sung giao diện vị trí liên tục có giới hạn; API hướng định sẵn không đủ cho smooth pursuit.
- [ ] Thiết kế state khởi đầu: `IDLE`, `ACQUIRE`, `FOLLOW`, `ENGAGED`, `RELEASE`, `DEGRADED`.
- [ ] Phân biệt attention mode `OBSERVE`/`INTERACT` với animation state; tránh tạo state cho mọi tổ hợp.
- [ ] Cho blink chạy đồng thời; saccade, fixation và pursuit là cách điều khiển gaze.
- [ ] Tắt random idle repositioning khi đang follow/engaged; chỉ một thành phần quyết định gaze đích tại một thời điểm.
- [ ] Kiểm chứng tác động smoothing của RoboEyes cùng filtering perception; giới hạn tổng độ trễ.
- [ ] Chạy renderer mục tiêu 30 FPS độc lập với inference; thử 60 FPS sau khi đo CPU.
- [ ] Dùng random seed để replay; one-shot reaction có cooldown và không restart ở mỗi observation.
- [ ] Đánh giá chuyển biểu cảm, blink, gaze motion bằng event replay trước khi ghép webcam live.

**Điều kiện hoàn thành:** simulator thể hiện được idle, acquire, follow, release và degraded; inference chậm hoặc tạm dừng không làm animation dừng theo.

## M5 — Attention quan sát và interaction lock

- [ ] Trong `OBSERVE`, định nghĩa utility score cùng hysteresis và thời gian giữ target tối thiểu.
- [ ] Thiết kế acquire interaction lock từ cues ổn định; không lock chỉ vì mặt lớn hoặc hướng đầu về camera.
- [ ] Chốt điều kiện giữ lock, giảm confidence, grace period, release và camera failure override.
- [ ] Tách việc giữ target khỏi mức biểu cảm; không kích hoạt lại reaction acquire liên tục.
- [ ] Người xa hướng mặt về helmet: cho phép nhìn lại ngắn hoặc tiếp tục idle.
- [ ] Walk-by: theo ngắn rồi release, tùy confidence và trạng thái hiện tại.
- [ ] Approaching estimate: tăng ưu tiên quan sát khi có bằng chứng đủ ổn định.
- [ ] Interaction candidate được acquire: giữ focus; scoring thông thường không tự giành lock.
- [ ] Target rời đi: release theo điều kiện đã chốt rồi trở lại observe/idle.
- [ ] Đánh giá false acquire, lock nhầm và lock tồn tại quá lâu trên video chưa dùng chỉnh tham số.
- [ ] Quyết định cơ chế người đội chủ động giữ/nhả target: chọn cách điều khiển hoặc ghi rõ defer và hạn chế tương ứng.
- [ ] Ghi lý do acquire/hold/release và thời gian chuyển mode để review.

**Điều kiện hoàn thành:** baseline một target có acquire/hold/release rõ ràng; lock không đồng nghĩa với nhận biết chắc chắn ý định trò chuyện; người đội vẫn quyết định tương tác thực tế.

## M6 — Nhiều người và cạnh tranh attention

- [ ] Cho perception trả tất cả face detections cần thiết; không chỉ lấy detection tốt nhất trước tracking.
- [ ] Kiểm chứng association và ID continuity khi người đi ngang nhau hoặc che khuất nhau.
- [ ] Đánh giá centroid/Kalman baseline trước khi thêm tracker phức tạp hơn.
- [ ] Kiểm chứng chi phí landmarks nhiều người; so sánh với chỉ xử lý target/candidate khi phù hợp.
- [ ] Áp dụng temporal filtering theo track; không giả định multi-face output đã được smoothing.
- [ ] Người đi ngang có mặt lớn hơn/confidence tốt hơn không tự chiếm interaction lock.
- [ ] Không chuyển lock sang người mới chỉ vì thứ tự detection hoặc track ID bị đổi.
- [ ] Kiểm chứng target mất tạm thời cạnh người khác, target rời đi và hai interaction candidates đồng thời.
- [ ] Đo target switches, switches ngoài ý muốn, ID switches, thời gian giữ target và false lock.

**Điều kiện hoàn thành:** các tình huống 2–3 người có kết quả giải thích được; interaction lock ổn định và release đúng chính sách đã chốt.

## M7 — Tăng độ khó môi trường

- [ ] Low light/ngược sáng: đo detection quality, false events và degraded behavior.
- [ ] Occlusion dài hơn, frame drop và inference overload: kiểm chứng freshness timeout và giới hạn prediction.
- [ ] Kiểm chứng camera failure/recovery khi đang lock; không tự phục hồi bằng observation cũ.
- [ ] Nếu giữ motion fallback: phân biệt motion với face/person evidence, đo false reactions và CPU tăng thêm.
- [ ] Sau khi baseline ổn định, quyết định scope riêng cho camera rotation và chuyển động đầu người đội.
- [ ] Trong scope motion được chấp thuận: kiểm chứng global motion, motion gating và nhu cầu IMU trước khi thêm hardware.
- [ ] Sau khi core behavior ổn định, thử habituation và gaze aversion; đo xem có làm giảm chất lượng focus không.
- [ ] Chạy regression trên bộ tình huống trước đó khi thêm behavior mới.

**Điều kiện hoàn thành:** các điều kiện môi trường đã chọn có tiêu chí pass và fallback rõ; hạng mục camera/helmet motion được ghi là đã kiểm chứng hoặc defer có chủ đích.

## M8 — Benchmark Raspberry Pi 5 và quyết định camera

- [ ] Khi được yêu cầu và có phần cứng, chạy cùng model, video, tham số và random seed trên Pi 5.
- [ ] Đo perception riêng và pipeline đầy đủ: CPU, CPU time/inference, RAM, latency, FPS và reaction latency.
- [ ] Đo nhiệt, throttling, mức ổn định khi chạy dài và công suất với phương pháp/thiết bị đo được ghi rõ.
- [ ] Đánh giá RAM thực tế để quyết định Pi 5 4 GB có đủ dư địa cho OS, perception và renderer hay không.
- [ ] Kiểm chứng capture với camera thực; không suy chất lượng camera từ video laptop.
- [ ] Xác định tỷ trọng bottleneck: capture, detection, landmarks, association, attention hay rendering.
- [ ] Chốt conventional camera nếu pipeline đạt yêu cầu và nhu cầu hình ảnh phù hợp.
- [ ] Chỉ đánh giá IMX500 khi có workload có thể offload và lợi ích dự kiến đáng kiểm chứng.
- [ ] Nếu thử IMX500: kiểm tra model compatibility, conversion, post-processing, chất lượng sau quantization và hiệu năng toàn pipeline.
- [ ] Ghi quyết định Camera Module 3 / IMX500 / cần thí nghiệm thêm, cùng dữ liệu hỗ trợ.

**Điều kiện hoàn thành:** có kết quả trên thiết bị đích và quyết định phần cứng dựa trên dữ liệu. Benchmark laptop không dùng để suy trực tiếp công suất hoặc FPS của Pi/IMX500.

## Protocol đo và mục tiêu thử nghiệm

| Metric | Cách sử dụng |
|---|---|
| CPU process và CPU time/inference | Ghi cách chuẩn hóa CPU %, số thread, workload và nhịp xử lý |
| Peak RAM | Ghi phạm vi process/child process; tránh cộng RSS làm trùng shared memory |
| P50/P95/P99 processing latency | Đo preprocessing/inference/post-processing; tách cold start khỏi steady state |
| Completed result FPS | Đếm kết quả thực sự hoàn thành; không dùng số lần gọi API async |
| Observation age | Thời điểm tiêu thụ result trừ timestamp capture; phát hiện buffering |
| Reaction latency | Mốc event được gán nhãn đến animation phản ứng; ghi sai số đo |
| Gaze jitter và pursuit lag | Đánh giá target đứng yên riêng với target chuyển động; không tính idle scan là jitter |
| False reactions / false locks | Đếm theo tình huống và thời lượng thử, kèm lý do |
| Target/ID switches | Phân biệt chuyển có chủ đích, đổi ngoài ý muốn và lỗi association |
| Temperature / power | Đo trên từng thiết bị; ghi điều kiện làm mát, display và tải nền |

Điểm xuất phát để thống nhất tiêu chí pass trước benchmark:

- Một cấu hình đạt khoảng 10 completed perception results/giây và renderer 30 FPS trong kịch bản đã chọn.
- P95 reaction latency mục tiêu khoảng 300 ms hoặc thấp hơn, bao gồm filtering và state transition.
- Không có frame backlog tăng dần hoặc observation quá cũ được sử dụng vượt ngưỡng.
- Không đổi target ngoài ý muốn trong bài thử target đứng yên một phút; đánh giá nhiều người riêng ở M6.
- Camera failure dẫn đến degraded behavior trong timeout đã định; mất target dùng release policy riêng.
- Chạy liên tục khoảng 30 phút để kiểm tra RAM, frame timing và suy giảm hiệu năng.

Đây là mục tiêu đề xuất. Có thể điều chỉnh trước khi đánh giá chính thức; mọi thay đổi phải được ghi lại, không đổi ngưỡng âm thầm sau khi thấy kết quả.

## Các quyết định còn mở

- Detector/model và phiên bản cuối cùng cho baseline.
- Head-pose method, attention thresholds và nhu cầu eye gaze.
- Utility weights, target-switch margin và minimum dwell time.
- Interaction acquire/release conditions, lock timeout và quyền override của người đội.
- Grace period cho occlusion và timeout cho observation freshness/camera failure.
- Phương án desktop adapter/port RoboEyes và cách điều khiển gaze liên tục.
- Scope camera/helmet motion sau baseline.
- Camera, accelerator và display vật lý sau benchmark thiết bị đích.

## Checkpoint tiếp theo cần ưu tiên

1. Chạy các lượt webcam 10/15 FPS và một phiên perception-only 10 FPS để đối chiếu với phiên có renderer; xác định nguồn CPU cao trên laptop trước khi kết luận workload phù hợp.
2. Lặp cùng tình huống webcam trực tiếp, ghi ánh sáng/khoảng cách/chế độ nguồn nếu biết và quan sát chất lượng tracking; video có nhãn bổ sung sau.
3. Chạy OpenCV DNN trên cùng webcam/điều kiện và triển khai phép đo Face Landmarker một người khi được yêu cầu.
4. Hoàn thiện track identity, confidence/freshness và target loss ở M2 trước khi mở rộng attention/interaction behavior.

Sau khi pipeline laptop đủ ổn định mới chuyển sang đánh giá Raspberry Pi và camera thực ở M8.

Chưa có bằng chứng để đánh dấu milestone hoàn thành, chốt camera/accelerator hoặc suy hiệu năng Raspberry Pi từ các phiên laptop hiện tại.

## Sau MVP — Nhánh tùy chọn, chưa cam kết triển khai

- [ ] Chỉ mở thí nghiệm LLM/VLM khi baseline có replay, metrics và bộ tình huống đánh giá.
- [ ] LLM nhận structured events; nếu dùng VLM, kiểm chứng lợi ích bổ sung từ ảnh.
- [ ] Model đề xuất ý định cấp cao; Character Engine vẫn kiểm soát realtime, lock và fallback.
- [ ] So sánh với baseline về tính cách, mức phù hợp, độ phong phú, latency, CPU/RAM và điện năng.
- [ ] Chỉ tích hợp khi lợi ích rõ; không mở rộng mặc định sang audio hoặc conversational AI.

## Nguồn tham chiếu

- [Raspieyes](https://github.com/alevizio/raspieyes) — baseline capture/detection và tham khảo tracking/rendering.
- [RoboEyes](https://github.com/FluxGarage/RoboEyes) — animation primitives, expression và transitions.
- [MediaPipe Face Detector](https://developers.google.com/edge/mediapipe/solutions/vision/face_detector) — model và task documentation.
- [MediaPipe Face Landmarker Python](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker/python) — running modes, outputs và multi-face configuration.
- [MediaPipe samples](https://github.com/google-ai-edge/mediapipe-samples) — ví dụ tham khảo desktop/Raspberry Pi.
- [Raspberry Pi AI Camera](https://www.raspberrypi.com/documentation/accessories/ai-camera.html) — IMX500 deployment và post-processing.

Kiểm tra lại source/documentation ở phiên bản đã chốt khi triển khai; các link theo branch có thể thay đổi.

## Nhật ký checkpoint và quyết định

| Ngày | Milestone / checkpoint | Cấu hình / phiên bản | Bằng chứng / kết quả | Quyết định / hạn chế | Bước tiếp theo |
|---|---|---|---|---|---|
| 2026-10-13 | Tạo roadmap | Chưa có implementation | Context và hướng thiết kế đã thống nhất; chưa đo hiệu năng | Laptop CPU local; CV + tracking + attention + FSM + RoboEyes; defer LLM/VLM | M0 khi được yêu cầu |
| 2026-10-14 | Runner M0–M1 | Raspieyes baseline có observer hooks; MediaPipe 0.10.21; NumPy 1.26.4; OpenCV 4.11.0.86; Pygame 2.6.1 | 8 kiểm tra kỹ thuật pass, gồm headless rendering, DNN/MediaPipe trên video giả lập, lỗi nguồn và signal shutdown | Kiểm tra kỹ thuật không xác nhận chất lượng tracking thực tế | Chạy webcam trên laptop |
| 2026-10-14 | Chạy thử 3 modes | Core 7 240H, 16 logical CPUs; webcam 0, 640×480; render target 30 FPS; motion fallback tắt | [Mouse](benchmark/mouse_20261014T073552_832839Z.json): đo 3.54 s, render 30.23 FPS. [Webcam](benchmark/webcam_20261014T073611_103681Z.json): đo 1.97 s, detection 9.66 FPS, render 30.01 FPS. [Benchmark](benchmark/benchmark_20261014T073842_355751Z.json): mới lượt 5 FPS, đo 12.59 s, detection 4.92 FPS, render 29.94 FPS. Không ghi capture failure | Cả 3 phiên `interrupted/user_stop`. CPU process trung bình webcam 1231.6%, benchmark 710.8% theo thang 100%=1 logical CPU; nguyên nhân chưa xác định. Chưa có lượt benchmark 10/15 FPS hoặc đánh giá chất lượng có nhãn | Hoàn tất lượt 5/10/15 và so sánh perception-only; ghi quan sát trực tiếp về hướng mắt/jitter/lag |
| 2026-10-14 | Publish baseline | Public repo nyclone569/FaceTracing; branch feat/laptop-benchmark; commit 1bf2fa0 | Runner/config/docs/patch đã push; source dependency, environment và raw benchmark JSON bị ignore. Fresh checkout + patch + project files pass 8 tests | Chưa tích hợp RoboEyes/Attention/FSM; tests dùng video giả lập không xác nhận face tracking thực tế | Tiếp tục các phép đo M0–M1 và điều tra CPU cao |
| 2026-10-14 | Làm rõ scope M0–M1 | Laptop CPU + webcam; RoboEyes pin v1.1.2/a35185d; default benchmark rates 10/15 | Roadmap và hướng dẫn tách phép đo laptop với xác nhận thiết bị đích; config có test_context để ghi khoảng cách/ánh sáng thủ công | Pi/camera helmet và video có nhãn defer. Khoảng cách thực chưa được đo; Face Landmarker chưa triển khai; chưa có kết quả 10/15 mới | Chạy DNN/MediaPipe live và perception-only; sau đó kiểm chứng landmarks |
