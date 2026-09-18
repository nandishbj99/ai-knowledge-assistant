package com.knowledgeassistant.web.dto;

import java.util.UUID;

public record DocumentStatusResponse(
        UUID id,
        String status,
        Integer totalParentChunks,
        Integer totalChildChunks,
        String errorMessage
) {}
