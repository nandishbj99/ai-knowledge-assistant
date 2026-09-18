package com.knowledgeassistant.web.dto;

import java.time.Instant;
import java.util.UUID;

public record ChatMessageResponse(
        UUID id,
        UUID sessionId,
        String sender,
        String content,
        String citations,
        Instant createdAt
) {}
