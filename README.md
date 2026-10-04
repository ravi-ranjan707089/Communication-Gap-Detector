# Communication Gap Detector

## Cerebro Neural Sentiment Hackathon 2026

### Problem Statement

**Detecting Communication Gaps in Group Conversations**

Group conversations often contain unanswered questions, repeated requests, repeated clarification attempts, and topics that remain unresolved. These gaps can cause confusion, delays, and incomplete tasks.

The Communication Gap Detector analyzes a conversation and identifies such patterns automatically.

---

## Our Solution

We developed a rule-based NLP system that processes a sequence of group messages and detects potential communication gaps.

The system analyzes:

- Message sequence
- Speaker identity
- Questions
- Requests
- Clarification attempts
- Responses
- Repeated messages
- Completion indicators

For every detected gap, the system provides:

- Gap type
- Speaker
- Message ID
- Original message
- Evidence
- Explanation
- Related/repeated message when applicable

---

## Key Features

### 1. Potentially Unanswered Questions

Detects questions where no relevant response is found within a defined message window.

Example:

```text
Neha: What time is the meeting?
Ravi: I am working on the report.
Soham: Can you send the dataset?
```
