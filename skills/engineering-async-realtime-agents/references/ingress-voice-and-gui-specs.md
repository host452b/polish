# Unified Event Ingress, Voice Timing Math & Computer Use Grounding Specs

## 1. Unified Event Envelope & Multi-Source Semantics (Ch.6)

```json
{
  "id": "evt_7f3a",
  "source": {"type": "app_chat", "sender": "user:u_5521", "verified": true},
  "dedupe_key": "app:msg:msg_1029",
  "thread": "app:conv:conv_88",
  "kind": "message",
  "correlation": ["order:12345"],
  "content": {"type": "text", "text": "这个订单我想退款"},
  "raw_ref": "raw/2026-11-23/app/msg_1029.json",
  "reply": {"via": "app_chat", "target": "app:conv:conv_88"},
  "occurred_at": "2026-11-23T14:02:09+08:00",
  "expires_at": null
}
```

| Source | Ordering Scope (`thread`) | Native Dedupe Key | ACK Window / Rule |
|---|---|---|---|
| App Chat | Conversation ID | Client `msg_id` (user saying "refund" twice = 2 distinct msgs) | Client receipt after inbox write |
| Feishu / WeCom | Unordered across events | `event_id` / `msg_id` | **ACK `<3s` (Feishu) / `<5s` (WeCom)** after inbox write |
| Webhook (Stripe/GitHub) | Unordered (use `occurred_at`/version) | Delivery ID or business `refund_id:status` | Return `2xx` immediately after inbox write |
| SQS (Std / FIFO) | FIFO: `MessageGroupId` | `MessageId` / `MessageDeduplicationId` | Delete message **after** inbox write (before visibility timeout) |
| Kafka | Partition key | `topic:partition:offset` (or business key in consumer store) | Commit offset after inbox write |

## 2. Voice Latency & Queueing Equations (Ch.6)

- **M/M/1 Queueing Blow-up:** $W = \frac{S}{1 - \rho}$. At service time $S = 1\text{s}$, utilization $\rho: 0.5 \to 0.8$ inflates total wait from $2\text{s} \to 5\text{s}$ ($3\text{s}$ pure queue wait).
- **Direct vs. Delegated Voice Tool Call:**
  - Direct foreground tool call: $\approx 2L_f + T$ (Exp 6-7 weather median: `2.81s`).
  - Slow-backend delegated tool call: $\approx 2L_f + 2L_b + T$ (Exp 6-7 median: `6.96s`).
  - Pre-loaded resident context: $\approx L_f$.

## 3. Computer Use Coordinate Reverse-Mapping (Ch.6)

When scaling a desktop of $(W_{\text{real}}, H_{\text{real}})$ into a model input of $(W_{\text{img}}, H_{\text{img}})$ with letterbox padding $(P_x, P_y)$:
$$x_{\text{real}} = (x_{\text{pred}} - P_x) \times \frac{W_{\text{real}}}{W_{\text{img}} - 2P_x}, \qquad y_{\text{real}} = (y_{\text{pred}} - P_y) \times \frac{H_{\text{real}}}{H_{\text{img}} - 2P_y}$$
Never stretch aspect ratios non-uniformly; pick the closest matching target aspect ratio (e.g., `1366×768` FWXGA for `2560×1440` 16:9).
