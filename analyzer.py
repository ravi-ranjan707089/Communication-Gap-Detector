import re

WINDOW_SIZE = 3

# 1. Parse conversation
def parse_messages(text):
    messages = []

    for line in text.splitlines():
        line = line.strip()

        if not line or ":" not in line:
            continue

        speaker, message = line.split(":", 1)

        messages.append({
            "id": len(messages) + 1,
            "speaker": speaker.strip(),
            "text": message.strip()
        })

    return messages


# -----------------------------
# 2. Normalize text
# -----------------------------
def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# -----------------------------
# 3. Detect questions
# -----------------------------
def is_question(text):
    return text.strip().endswith("?")


# -----------------------------
# 4. Detect requests
# -----------------------------
def is_request(text):
    text = text.lower()

    request_patterns = [
        "please",
        "can you",
        "could you",
        "would you",
        "send",
        "share",
        "give me",
        "tell me",
        "let me know",
        "provide"
    ]

    return any(pattern in text for pattern in request_patterns)


# -----------------------------
# 5. Detect clarification
# -----------------------------
def is_clarification(text):
    text = text.lower()

    clarification_patterns = [
        "what do you mean",
        "can you clarify",
        "please clarify",
        "which one",
        "which file",
        "what exactly",
        "i don't understand",
        "i dont understand",
        "i still don't understand",
        "i still dont understand",
        "could you explain",
        "please explain",
        "can you explain",
        "which meeting",
        "which room"
    ]

    return any(
        pattern in text
        for pattern in clarification_patterns
    )

# -----------------------------
# 6. Check possible response
# -----------------------------
def is_possible_response(question, message):
    message_lower = message.lower()

    response_patterns = [
    r"\byes\b",
    r"\bno\b",
    r"\bthe meeting is\b",
    r"\bit is\b",
    r"\bit's\b",
    r"\bwill be\b",
    r"\bis at\b",
    r"\bare at\b",
    r"\bat \d",
    r"\b\d+\s*(am|pm)\b",
    r"\broom\s+\d+\b",
    r"\broom\s+[a-z]\b",
    r"\bsure\b",
    r"\bi will\b",
    r"\bi'll\b",
    r"\bgot it\b",
    r"\bthank you\b",
    r"\bthanks\b"
]

    for pattern in response_patterns:
        if re.search(pattern, message_lower):
            return True

    return False


# -----------------------------
# 7. Detect unanswered questions
# -----------------------------
def detect_unanswered_questions(messages, window_size=WINDOW_SIZE):

    gaps = []

    for i, current in enumerate(messages):

        if not is_question(current["text"]):
            continue

        # Requests such as "Can you send..." are handled separately
        if is_request(current["text"]):
            continue

        answered = False

        end = min(i + window_size + 1, len(messages))

        for j in range(i + 1, end):

            if is_possible_response(
                current["text"],
                messages[j]["text"]
            ):
                answered = True
                break

        if not answered:

            gaps.append({
                "type": "Potentially Unanswered Question",
                "speaker": current["speaker"],
                "message_id": current["id"],
                "message": current["text"],
                "evidence": (
                    f"No relevant response detected within "
                    f"{window_size} subsequent messages."
                ),
                "explanation": (
                    "The question was not followed by a message "
                    "matching the response rules within the defined window."
                )
            })

    return gaps


# -----------------------------
# 8. Check acknowledgement
# -----------------------------
def is_acknowledgement(text):

    text = normalize_text(text)

    acknowledgement_patterns = [
        "okay",
        "ok",
        "got it",
        "sure",
        "yes",
        "done",
        "will do",
        "i will",
        "i'll check",
        "noted",
        "understood"
    ]

    return any(
        pattern in text
        for pattern in acknowledgement_patterns
    )


# -----------------------------
# 9. Check completion
# -----------------------------
def is_completion(text):

    text = normalize_text(text)

    completion_patterns = [
    "done",
    "completed",
    "sent",
    "uploaded",
    "finished",
    "shared",
    "submitted",
    "send",
    "sending",
    "i have sent",
    "i sent",
    "already sent",
    "i will send",
    "i'll send",
    "sure, i will send",
    "sure, i'll send"
]

    return any(
        pattern in text
        for pattern in completion_patterns
    )


# -----------------------------
# 10. Detect repeated requests
# -----------------------------
def detect_repeated_requests(messages, window_size=WINDOW_SIZE):

    gaps = []

    for i, current in enumerate(messages):

        if not is_request(current["text"]):
            continue

        current_normalized = normalize_text(current["text"])

        end = min(i + window_size + 1, len(messages))

        for j in range(i + 1, end):

            later = messages[j]

            # Must be the same participant
            if later["speaker"] != current["speaker"]:
                continue

            if not is_request(later["text"]):
                continue

            later_normalized = normalize_text(later["text"])

            # Exact normalized match for MVP
            if current_normalized != later_normalized:
                continue

            acknowledged = False
            completed = False

            # Check messages between the two requests
            for k in range(i + 1, j):

                intermediate = messages[k]["text"]

                if is_completion(intermediate):
                    completed = True

                if is_acknowledgement(intermediate):
                    acknowledged = True

            # If request was acknowledged but not completed,
            # it can still be a repeated request.
            if not completed:

                gaps.append({
                    "type": "Repeated Request",
                    "speaker": current["speaker"],
                    "message_id": current["id"],
                    "message": current["text"],
                    "repeated_at": later["id"],
                    "evidence": (
                        f"Same participant repeated the request "
                        f"at message {later['id']}."
                    ),
                    "explanation": (
                        "The same request was repeated before "
                        "a clear completion was detected."
                    )
                })

            break

    return gaps


# -----------------------------
# 11. Detect repeated clarifications
# -----------------------------
def detect_repeated_clarifications(
    messages,
    window_size=WINDOW_SIZE
):

    gaps = []

    for i, current in enumerate(messages):

        if not is_clarification(current["text"]):
            continue

        end = min(i + window_size + 1, len(messages))

        for j in range(i + 1, end):

            later = messages[j]

            if later["speaker"] != current["speaker"]:
                continue

            if not is_clarification(later["text"]):
                continue

            gaps.append({
                "type": "Repeated Clarification",
                "speaker": current["speaker"],
                "message_id": current["id"],
                "message": current["text"],
                "repeated_at": later["id"],
                "evidence": (
                    f"The participant requested clarification "
                    f"again at message {later['id']}."
                ),
                "explanation": (
                    "The participant made another clarification "
                    "request, indicating that the earlier "
                    "explanation may not have resolved the issue."
                )
            })

            break

    return gaps


# -----------------------------
# 12. Detect unresolved topics
# -----------------------------
def detect_unresolved_topics(messages):

    topics = []

    completion_words = [
        "sent",
        "shared",
        "uploaded",
        "submitted",
        "completed",
        "done",
        "finished",
        "provided"
    ]

    for i, current in enumerate(messages):

        if not is_request(current["text"]):
            continue

        current_normalized = normalize_text(
            current["text"]
        )

        # Look for a repeated request
        for j in range(i + 1, len(messages)):

            later = messages[j]

            if later["speaker"] != current["speaker"]:
                continue

            if not is_request(later["text"]):
                continue

            later_normalized = normalize_text(
                later["text"]
            )

            if current_normalized != later_normalized:
                continue

            # Check whether the request was completed
            completed = False

            for k in range(i + 1, j):

                message_text = messages[k]["text"].lower()

                for word in completion_words:

                    if word in message_text:
                        completed = True
                        break

                if completed:
                    break

            # If no completion was found,
            # mark it as an unresolved topic
            if not completed:

                topic = extract_topic(
                    current["text"]
                )

                topics.append({
                    "topic": topic,
                    "speaker": current["speaker"],
                    "message_id": current["id"],
                    "repeated_at": later["id"],
                    "evidence": (
                        f"The request about '{topic}' "
                        f"was repeated, but no clear completion "
                        f"was detected."
                    ),
                    "explanation": (
                        "The topic appears unresolved because "
                        "the participant repeated the request "
                        "without a detected completion."
                    )
                })

            break

    return topics


# -----------------------------
# 13. Extract simple topic
# -----------------------------
def extract_topic(text):

    text = text.lower()

    topic = text

    patterns = [
        "can you send",
        "could you send",
        "please send",
        "send",
        "can you share",
        "could you share",
        "please share",
        "share",
        "can you provide",
        "could you provide",
        "please provide",
        "provide"
    ]

    for pattern in patterns:

        if topic.startswith(pattern):

            topic = topic[
                len(pattern):
            ].strip()

            break

    topic = topic.rstrip("?")

    if not topic:
        topic = "the requested item"

    return topic

# -----------------------------
# 14. Complete analysis
# -----------------------------
def analyze_conversation(text):

    messages = parse_messages(text)

    unanswered_questions = detect_unanswered_questions(
        messages
    )

    repeated_requests = detect_repeated_requests(
        messages
    )

    repeated_clarifications = detect_repeated_clarifications(
        messages
    )

    unresolved_topics = detect_unresolved_topics(
        messages
    )

    gaps = (
        unanswered_questions
        + repeated_requests
        + repeated_clarifications
    )

    return {
        "messages": messages,
        "gaps": gaps,
        "unresolved_topics": unresolved_topics,
        "total_gaps": len(gaps),
        "total_unresolved_topics": len(unresolved_topics)
    }




# -----------------------------
# 15. Main
# -----------------------------
if __name__ == "__main__":

    with open(
        "data/conversation.txt",
        "r",
        encoding="utf-8"
    ) as file:

        conversation = file.read()

    result = analyze_conversation(conversation)

    print("\n" + "=" * 60)
    print("       COMMUNICATION GAP DETECTOR")
    print("=" * 60)

    print(
        f"\nMessages analyzed: "
        f"{len(result['messages'])}"
    )

    print(
        f"Communication gaps detected: "
        f"{result['total_gaps']}"
    )

    print(
        f"Unresolved topics detected: "
        f"{result['total_unresolved_topics']}"
    )

    print("\n" + "-" * 60)

    # -----------------------------
    # Communication gaps
    # -----------------------------

    if not result["gaps"]:

        print("No communication gaps detected.")

    else:

        for index, gap in enumerate(
            result["gaps"],
            start=1
        ):

            print(f"\nGAP #{index}")
            print(f"Type       : {gap['type']}")
            print(f"Speaker    : {gap['speaker']}")
            print(f"Message ID : {gap['message_id']}")
            print(f"Message    : {gap['message']}")

            if "repeated_at" in gap:

                print(
                    f"Repeated At: "
                    f"Message {gap['repeated_at']}"
                )

            print(
                f"Evidence   : "
                f"{gap['evidence']}"
            )

            print(
                f"Explanation: "
                f"{gap['explanation']}"
            )

            print("-" * 60)


    # -----------------------------
    # Unresolved topics
    # -----------------------------

    print("\n" + "=" * 60)
    print("              UNRESOLVED TOPICS")
    print("=" * 60)

    if not result["unresolved_topics"]:

        print("\nNo unresolved topics detected.")

    else:

        for index, topic in enumerate(
            result["unresolved_topics"],
            start=1
        ):

            print(f"\nTOPIC #{index}")

            print(
                f"Topic      : "
                f"{topic['topic']}"
            )

            print(
                f"Speaker    : "
                f"{topic['speaker']}"
            )

            print(
                f"Message ID : "
                f"{topic['message_id']}"
            )

            print(
                f"Repeated At: "
                f"Message {topic['repeated_at']}"
            )

            print(
                f"Evidence   : "
                f"{topic['evidence']}"
            )

            print(
                f"Explanation: "
                f"{topic['explanation']}"
            )

            print("-" * 60)