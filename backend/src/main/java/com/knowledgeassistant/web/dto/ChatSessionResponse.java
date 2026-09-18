package com.knowledgeassistant.web.dto;

import java.time.Instant;
import java.util.UUID;

public record ChatSessionResponse(
        UUID id,
        String title,
        Instant createdAt,
        Instant updatedAt
) {}
