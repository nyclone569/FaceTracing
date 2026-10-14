# Roadmap — AI-assisted Protogen Helmet

Ngày tạo: 2026-10-13

Trạng thái: đã triển khai công cụ và chạy thử mouse/webcam/benchmark trên laptop; M0–M1 vẫn đang kiểm chứng, phiên benchmark hiện mới có lượt 5 FPS.

Cập nhật 2026-10-14: đã thêm laptop runner cho bước 5–6 tại [experiments/run_raspieyes.py](experiments/run_raspieyes.py), cấu hình và JSON metrics. Xem [hướng dẫn và điểm nối RoboEyes](experiments/README.md). Đây là công cụ kiểm chứng baseline; milestone chỉ được đánh dấu khi có đủ bằng chứng theo tiêu chí bên dưới.

Quyết định quản lý source: `raspieyes/` được ignore trong repo chính, tải riêng tại upstream commit cố định rồi áp dụng [patch benchmark hooks](patches/raspieyes-benchmark-hooks.patch). [Hướng dẫn cài đặt](experiments/README.md) mô tả cách tái tạo source trên máy mới. Các kết quả trong `benchmark/` là dữ liệu local, chưa được commit.

## Cách sử dụng

- `[ ]`: chưa hoàn thành; `[x]`: đã hoàn thành và có bằng chứng kiểm chứng.
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

| Hoàn thành | Milestone | Kết quả chính | Phụ thuộc |
|---|---|---|---|
| [ ] | M0 — Protocol và baseline | Bộ tình huống, cấu hình, metrics có thể so sánh | — |
| [ ] | M1 — Model trên laptop CPU | Chọn baseline detection và đo landmarking | M0 |
| [ ] | M2 — Tracking và độ tin cậy | Theo một người; xử lý stale, mất target, camera failure | M1 |
| [ ] | M3 — Attention cues | Kiểm chứng head orientation và event từ track history | M2 |
| [ ] | M4 — RoboEyes và Character State Machine | Simulator animation độc lập với perception | M2; dùng cues M3 khi sẵn sàng |
| [ ] | M5 — Interaction lock | Acquire, giữ và release một target có giải thích | M3, M4 |
| [ ] | M6 — Nhiều người và attention competition | Chống đổi target ngoài ý muốn | M5 |
| [ ] | M7 — Môi trường và degraded behavior | Low light, occlusion, frame drop; camera motion theo scope riêng | M6 |
| [ ] | M8 — Raspberry Pi 5 và quyết định camera | Benchmark thiết bị đích, chọn hướng phần cứng bằng dữ liệu | M7; phần cứng được phép sử dụng |

M0–M5 tạo baseline hành vi trên laptop. M6–M7 tăng độ phức tạp và kiểm chứng tính ổn định. M8 xác nhận khả năng chạy trên thiết bị đích.

## M0 — Chuẩn bị protocol và baseline

- [ ] Ghi CPU, OS, số core/thread, webcam, chế độ nguồn và phiên bản Python dự kiến.
- [ ] Chốt commit Raspieyes, RoboEyes, phiên bản MediaPipe và model assets dùng trong thử nghiệm.
- [ ] Kiểm tra license của code, dependencies và model trước khi chốt phương án tái sử dụng.
- [ ] Phân biệt component đã có trong repo với chức năng còn cần bổ sung; không suy từ README rằng mọi tính năng đã hoạt động.
- [ ] Chuẩn bị video: không người, một người, walk-by, nhìn camera, quay mặt, tiếp cận và rời đi.
- [ ] Ghi độ phân giải, FPS, khoảng cách thử và ánh sáng; gán nhãn mốc event để đo reaction latency.
- [ ] Tách tập dùng chỉnh tham số khỏi tập dùng đánh giá.
- [ ] Chốt cách đo CPU, RAM, latency, completed result FPS và độ tuổi observation.

**Điều kiện hoàn thành:** có protocol chạy lại được; mọi kết quả sau này gắn với cấu hình và phiên bản cụ thể.

## M1 — Kiểm chứng model trên laptop CPU

- [x] Chạy baseline MediaPipe Face Detector / BlazeFace từ Raspieyes. Bằng chứng: webcam 10 FPS và benchmark 5 FPS ngày 2026-10-14, camera 0, ảnh thực tế 640×480; các phiên dừng chủ động.
- [ ] Chạy OpenCV DNN detector trong Raspieyes làm đối chứng.
- [x] Ghi detector thực sự hoạt động, kể cả khi fallback; không gộp kết quả khác detector. Các phiên webcam/benchmark hiện tại ghi `actual_detector=mediapipe`, motion fallback tắt.
- [ ] Đo Face Landmarker một khuôn mặt độc lập trước khi thêm detector riêng phía trước.
- [ ] Thử inference mục tiêu 5, 10, 15 FPS; capture khởi đầu 640×480 và mục tiêu 30 FPS nếu webcam hỗ trợ.
- [ ] Đo perception riêng; đo lại với preview/simulator để thấy overhead hiển thị.
- [ ] Ghi P50/P95/P99 processing latency, CPU time/inference, CPU process, peak RAM, completed FPS và dropped/skipped frames.
- [ ] Đánh giá miss detection, false detection, face box jitter và ảnh hưởng của mặt nhỏ/quay nghiêng.
- [ ] Chọn detector baseline dựa trên chất lượng và chi phí; ghi rõ giới hạn của model chưa chọn.

**Điều kiện hoàn thành:** có bảng so sánh từ cùng input; xác định cấu hình khả thi để bước sang tracking. Nếu chưa đạt nhịp mong muốn, ghi bottleneck và cấu hình giảm tải trước khi cân nhắc accelerator.

## M2 — Face tracking một người và reliability tối thiểu

- [ ] Kiểm tra đường dữ liệu thực tế trong Raspieyes: detection, EMA/dead zone, tracker và target output.
- [ ] Chuẩn hóa observation: timestamp capture, timestamp result, face position/size và thông tin chất lượng sẵn có.
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
