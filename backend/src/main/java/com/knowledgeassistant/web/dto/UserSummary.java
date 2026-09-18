package com.knowledgeassistant.web.dto;

import java.util.UUID;

public record UserSummary(
        UUID id,
        UUID tenantId,
        String email,
        String fullName,
        String role
) {}
