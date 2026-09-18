package com.knowledgeassistant.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.knowledgeassistant.domain.entity.ChatMessage;
import com.knowledgeassistant.security.UserPrincipal;
import com.knowledgeassistant.web.dto.ChatDto.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.*;

@Service
public class RAGService {

    private static final Logger log = LoggerFactory.getLogger(RAGService.class);

    private final ChatSessionService chatSessionService;
    private final RestClient restClient;
    private final ObjectMapper objectMapper;

    public RAGService(
            ChatSessionService chatSessionService,
            @Value("${app.ai-service.base-url:http://localhost:8001}") String aiServiceBaseUrl,
            ObjectMapper objectMapper) {
        this.chatSessionService = chatSessionService;
        this.restClient = RestClient.builder().baseUrl(aiServiceBaseUrl).build();
        this.objectMapper = objectMapper;
    }

    public ChatQueryResponse askQuestion(UUID sessionId, UserPrincipal principal, ChatQueryRequest request) {
        // 1. Verify session exists and belongs to user
        chatSessionService.getSession(sessionId, principal.getId(), principal.getTenantId());

        // 2. Fetch recent conversation context (sliding window, max 6 messages)
        List<ChatMessage> contextMessages = chatSessionService.getRecentContext(sessionId, principal.getId(), principal.getTenantId(), 6);
        List<Map<String, String>> historyList = new ArrayList<>();
        for (ChatMessage msg : contextMessages) {
            historyList.add(Map.of("sender", msg.getSender(), "content", msg.getContent()));
        }

        // 3. Persist user message in chat history
        chatSessionService.addMessage(sessionId, principal.getId(), principal.getTenantId(), "USER", request.query(), "[]");

        // 4. Call Python AI Microservice /query
        AiServiceQueryPayload payload = new AiServiceQueryPayload(
                request.query(),
                sessionId.toString(),
                principal.getId().toString(),
                principal.getTenantId().toString(),
                historyList
        );

        String answer;
        List<Map<String, Object>> citations = Collections.emptyList();
        String citationsJson = "[]";

        try {
            AiServiceQueryResponse aiResponse = restClient.post()
                    .uri("/query")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(payload)
                    .retrieve()
                    .body(AiServiceQueryResponse.class);

            if (aiResponse != null) {
                answer = aiResponse.answer();
                if (aiResponse.citations() != null) {
                    citations = aiResponse.citations();
                    citationsJson = objectMapper.writeValueAsString(citations);
                }
            } else {
                answer = "I could not retrieve an answer at this time.";
            }
        } catch (Exception e) {
            log.error("Error communicating with AI microservice", e);
            answer = "The AI service is currently unavailable or encountered an error processing your query.";
        }

        // 5. Persist assistant response with citations
        chatSessionService.addMessage(sessionId, principal.getId(), principal.getTenantId(), "ASSISTANT", answer, citationsJson);

        return new ChatQueryResponse(sessionId, answer, citations);
    }
}
