package com.knowledgeassistant.web.controller;

import com.knowledgeassistant.security.UserPrincipal;
import com.knowledgeassistant.service.RAGService;
import com.knowledgeassistant.web.dto.ChatDto.ChatQueryRequest;
import com.knowledgeassistant.web.dto.ChatDto.ChatQueryResponse;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/chat/sessions")
public class ChatQueryController {

    private final RAGService ragService;

    public ChatQueryController(RAGService ragService) {
        this.ragService = ragService;
    }

    @PostMapping("/{sessionId}/query")
    public ResponseEntity<ChatQueryResponse> askQuestion(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID sessionId,
            @Valid @RequestBody ChatQueryRequest request) {
        ChatQueryResponse response = ragService.askQuestion(sessionId, principal, request);
        return ResponseEntity.ok(response);
    }
}
