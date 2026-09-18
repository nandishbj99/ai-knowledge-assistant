package com.knowledgeassistant.web.controller;

import com.knowledgeassistant.security.UserPrincipal;
import com.knowledgeassistant.service.ChatSessionService;
import com.knowledgeassistant.web.dto.ChatMessageResponse;
import com.knowledgeassistant.web.dto.ChatSessionResponse;
import com.knowledgeassistant.web.dto.CreateSessionRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/chat/sessions")
public class ChatSessionController {

    private final ChatSessionService chatSessionService;

    public ChatSessionController(ChatSessionService chatSessionService) {
        this.chatSessionService = chatSessionService;
    }

    @PostMapping
    public ResponseEntity<ChatSessionResponse> createSession(
            @AuthenticationPrincipal UserPrincipal principal,
            @RequestBody(required = false) CreateSessionRequest request) {
        ChatSessionResponse response = chatSessionService.createSession(principal.getId(), principal.getTenantId(), request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping
    public ResponseEntity<List<ChatSessionResponse>> getSessions(@AuthenticationPrincipal UserPrincipal principal) {
        List<ChatSessionResponse> sessions = chatSessionService.getSessions(principal.getId(), principal.getTenantId());
        return ResponseEntity.ok(sessions);
    }

    @GetMapping("/{id}")
    public ResponseEntity<ChatSessionResponse> getSession(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID id) {
        ChatSessionResponse session = chatSessionService.getSession(id, principal.getId(), principal.getTenantId());
        return ResponseEntity.ok(session);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Map<String, String>> deleteSession(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID id) {
        chatSessionService.deleteSession(id, principal.getId(), principal.getTenantId());
        return ResponseEntity.ok(Map.of("message", "Chat session deleted successfully"));
    }

    @GetMapping("/{id}/messages")
    public ResponseEntity<List<ChatMessageResponse>> getMessages(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID id) {
        List<ChatMessageResponse> messages = chatSessionService.getMessages(id, principal.getId(), principal.getTenantId());
        return ResponseEntity.ok(messages);
    }
}
