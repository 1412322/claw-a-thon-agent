# Đặc tả Tính năng Nạp Tiền Điện Thoại — ZaloPay

## Tổng quan
Cho phép user nạp tiền trực tiếp vào số điện thoại thuộc các nhà mạng 
Viettel, Mobifone, Vinaphone, Vietnamobile, Gmobile thông qua ZaloPay.

## API Endpoint
POST /api/v1/topup/request

## Input
- phone_number: string (10 số, bắt buộc)
- carrier: enum [VIETTEL, MOBIFONE, VINAPHONE, VIETNAMOBILE, GMOBILE, GMOBILE123]
- amount: enum [10000, 20000, 50000, 100000, 200000, 500000] (VND)
- payment_source: enum [ZALOPAY_WALLET, LINKED_BANK, ATM_CARD]
- idempotency_key: string (UUID, bắt buộc trong Header)

## Business Rules
- Tự động nhận diện nhà mạng từ đầu số điện thoại
  + Viettel: 032, 033, 034, 035, 036, 037, 038, 039, 086, 096, 097, 098
  + Mobifone: 070, 079, 077, 076, 078, 089, 090, 093
  + Vinaphone: 081, 082, 083, 084, 085, 088, 091, 094
  + Vietnamobile: 052, 056, 058, 092
  + Gmobile: 059, 099
  + Gmobile123: 0592, 0992
- Số dư ZaloPay Wallet phải đủ trước khi gọi nhà mạng
- Idempotency-Key bắt buộc để tránh nạp trùng khi retry
- Timeout từ nhà mạng sau 15 giây → trạng thái PENDING
- Giao dịch PENDING sẽ được reconcile tự động sau 5 phút
- Nếu reconcile thất bại sau 3 lần retry → chuyển FAILED, hoàn tiền tự động
- Giới hạn: 10 giao dịch nạp tiền/ngày/tài khoản
- Giới hạn: tối đa 2,000,000 VND/ngày/tài khoản

## Trạng thái Giao dịch
- PROCESSING: đang gửi yêu cầu đến nhà mạng
- PENDING: nhà mạng timeout, chờ reconcile
- SUCCESS: nạp thành công, nhà mạng xác nhận
- FAILED: nạp thất bại, đã hoàn tiền
- REFUNDED: đã hoàn tiền về nguồn thanh toán

## Error Codes
- TOP001: Số điện thoại không hợp lệ
- TOP002: Không nhận diện được nhà mạng
- TOP003: Mệnh giá không hỗ trợ
- TOP004: Số dư không đủ
- TOP005: Vượt giới hạn giao dịch ngày (10 lần)
- TOP006: Vượt hạn mức tiền ngày (2,000,000 VND)
- TOP007: Timeout nhà mạng → PENDING
- TOP008: Nhà mạng từ chối giao dịch
- TOP009: Duplicate request (Idempotency-Key đã tồn tại)

## Logging & Bảo mật
- Log: transaction_id, phone_masked (che 4 số giữa: 09xx***xx90), 
  carrier, amount, status, timestamp
- KHÔNG log: số tài khoản ngân hàng đầy đủ, OTP, CVV
- Mọi request phải có Authorization header (JWT Token)

## Màn hình & Flow UI
- Màn hình 1 — Nhập thông tin: ô nhập số điện thoại, 
  auto-detect nhà mạng hiển thị logo, chọn mệnh giá
- Màn hình 2 — Xác nhận: hiển thị tóm tắt giao dịch + số dư sau khi nạp
- Màn hình 3 — Nhập OTP: 6 số, hết hạn sau 3 phút
- Màn hình 4 — Kết quả: SUCCESS hiện confetti, 
  PENDING hiện thông báo "Đang xử lý, vui lòng chờ"
- PENDING polling: FE poll API /topup/status mỗi 10 giây, tối đa 3 phút