package com.knowledgeassistant.web.dto;

import jakarta.validation.constraints.NotBlank;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public class ChatDto {

    public record ChatQueryRequest(
            @NotBlank(message = "Query must not be empty") String query
    ) {}

    public record Citation(
            String sourceKey,
            UUID documentId,
            String filename,
            Integer pageNumber,
            String snippet
    ) {}

    public record ChatQueryResponse(
            UUID sessionId,
            String answer,
            List<Map<String, Object>> citations
    ) {}

    public record AiServiceQueryPayload(
            String query,
            String session_id,
            String user_id,
            String tenant_id,
            List<Map<String, String>> history
    ) {}

    public record AiServiceQueryResponse(
            String answer,
            List<Map<String, Object>> citations
    ) {}
}
