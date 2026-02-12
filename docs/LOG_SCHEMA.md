# Schema log và chuẩn hóa cho Vector DB

## 1. Format log gốc (từ Kafka)

Mỗi message là JSON với cấu trúc:

```json
{
  "startTime": 1770869240122,
  "module": "sb.MerchantProcessorV2",
  "operation": "/order/create",
  "requesterCode": "MERCHANT_PAYMENTGW_SERVICE",
  "opVer": "v1.0",
  "spanId": "94518c4c-3809-431f-b2ec-ff24b5d1d082",
  "requestId": "94518c4c-3809-431f-b2ec-ff24b5d1d082",
  "respCode": "OK",
  "data": { ... },
  "endTime": 1770869240303,
  "processingTime": 181
}
```

Trường `data` thay đổi theo từng module/operation, nhưng thường có các trường dùng để tra cứu:

- **orderNo** / **order_no** — mã đơn hàng (vd: `Y20KI9R6`)
- **orderId** — id nội bộ order
- **traceId** — id trace (có thể trùng requestId)
- **requestId** — id request (có thể có trong data hoặc top-level)
- **merchantId** — mã merchant
- **branchCode** — mã chi nhánh
- **amount** — số tiền
- **channel** — kênh (MBS, …)
- **status** — trạng thái (OPEN, PAYED, PROCESSING, …)
- **respCode** / **responseCode** — mã phản hồi (OK, …)

## 2. Schema chuẩn hóa (lưu Vector DB)

Mỗi bản ghi sau khi xử lý lưu vào Vector DB với:

| Trường | Kiểu | Mô tả |
|--------|------|--------|
| **id** | string | Id duy nhất (vd: `{requestId}_{startTime}` hoặc UUID) |
| **request_id** | string | requestId từ log |
| **order_no** | string | Mã đơn hàng (orderNo) |
| **order_id** | string | orderId (nếu có) |
| **trace_id** | string | traceId (nếu có) |
| **merchant_id** | string | merchantId |
| **branch_code** | string | branchCode |
| **amount** | number | amount |
| **channel** | string | channel |
| **module** | string | module từ log (vd: sb.MerchantProcessorV2) |
| **operation** | string | operation (vd: /order/create) |
| **resp_code** | string | respCode (OK, ERROR, …) |
| **status** | string | status trong data (OPEN, PAYED, …) |
| **timestamp** | int/string | startTime hoặc parse từ data.date |
| **processing_time_ms** | int | processingTime (ms) |
| **text** | string | Chuỗi dùng cho embedding: nối module, operation, orderNo, merchantId, respCode, status, (trích đoạn data) |
| **payload** | string | JSON string của log gốc (để hiển thị chi tiết khi cần) |

Vector DB dùng **metadata** (payload) để filter theo `order_no`, `merchant_id`, `request_id`, `trace_id`; dùng **vector** (embedding của `text`) cho semantic search (tùy chọn).
