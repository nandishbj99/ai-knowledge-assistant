package com.knowledgeassistant.web.dto;

import java.time.Instant;
import java.util.UUID;

public record DocumentResponse(
        UUID id,
        String filename,
        Long fileSize,
        String mimeType,
        String status,
        Integer totalParentChunks,
        Integer totalChildChunks,
        String errorMessage,
        Instant createdAt
) {}
