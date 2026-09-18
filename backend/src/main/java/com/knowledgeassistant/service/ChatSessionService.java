package com.knowledgeassistant.service;

import com.knowledgeassistant.domain.entity.ChatMessage;
import com.knowledgeassistant.domain.entity.ChatSession;
import com.knowledgeassistant.domain.repository.ChatMessageRepository;
import com.knowledgeassistant.domain.repository.ChatSessionRepository;
import com.knowledgeassistant.web.dto.ChatMessageResponse;
import com.knowledgeassistant.web.dto.ChatSessionResponse;
import com.knowledgeassistant.web.dto.CreateSessionRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class ChatSessionService {

    private final ChatSessionRepository sessionRepository;
    private final ChatMessageRepository messageRepository;

    public ChatSessionService(ChatSessionRepository sessionRepository, ChatMessageRepository messageRepository) {
        this.sessionRepository = sessionRepository;
        this.messageRepository = messageRepository;
    }

    @Transactional
    public ChatSessionResponse createSession(UUID userId, UUID tenantId, CreateSessionRequest request) {
        String title = (request != null && request.title() != null && !request.title().isBlank())
                ? request.title().trim()
                : "New Conversation";

        ChatSession session = new ChatSession(userId, tenantId, title);
        session = sessionRepository.save(session);

        return new ChatSessionResponse(session.getId(), session.getTitle(), session.getCreatedAt(), session.getUpdatedAt());
    }

    @Transactional(readOnly = true)
    public List<ChatSessionResponse> getSessions(UUID userId, UUID tenantId) {
        return sessionRepository.findAllByTenantIdAndUserIdOrderByUpdatedAtDesc(tenantId, userId)
                .stream()
                .map(s -> new ChatSessionResponse(s.getId(), s.getTitle(), s.getCreatedAt(), s.getUpdatedAt()))
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public ChatSessionResponse getSession(UUID sessionId, UUID userId, UUID tenantId) {
        ChatSession session = sessionRepository.findByIdAndTenantIdAndUserId(sessionId, tenantId, userId)
                .orElseThrow(() -> new NoSuchElementException("Chat session not found: " + sessionId));

        return new ChatSessionResponse(session.getId(), session.getTitle(), session.getCreatedAt(), session.getUpdatedAt());
    }

    @Transactional
    public void deleteSession(UUID sessionId, UUID userId, UUID tenantId) {
        ChatSession session = sessionRepository.findByIdAndTenantIdAndUserId(sessionId, tenantId, userId)
                .orElseThrow(() -> new NoSuchElementException("Chat session not found: " + sessionId));

        messageRepository.deleteAllBySessionId(sessionId);
        sessionRepository.delete(session);
    }

    @Transactional(readOnly = true)
    public List<ChatMessageResponse> getMessages(UUID sessionId, UUID userId, UUID tenantId) {
        // Verify session ownership
        sessionRepository.findByIdAndTenantIdAndUserId(sessionId, tenantId, userId)
                .orElseThrow(() -> new NoSuchElementException("Chat session not found: " + sessionId));

        return messageRepository.findAllBySessionIdAndTenantIdAndUserIdOrderByCreatedAtAsc(sessionId, tenantId, userId)
                .stream()
                .map(m -> new ChatMessageResponse(m.getId(), m.getSessionId(), m.getSender(), m.getContent(), m.getCitations(), m.getCreatedAt()))
                .collect(Collectors.toList());
    }

    @Transactional
    public ChatMessageResponse addMessage(UUID sessionId, UUID userId, UUID tenantId, String sender, String content, String citations) {
        ChatSession session = sessionRepository.findByIdAndTenantIdAndUserId(sessionId, tenantId, userId)
                .orElseThrow(() -> new NoSuchElementException("Chat session not found: " + sessionId));

        ChatMessage message = new ChatMessage(sessionId, userId, tenantId, sender, content, citations);
        message = messageRepository.save(message);

        // Update session timestamp
        session.onUpdate();
        sessionRepository.save(session);

        return new ChatMessageResponse(message.getId(), message.getSessionId(), message.getSender(), message.getContent(), message.getCitations(), message.getCreatedAt());
    }

    @Transactional(readOnly = true)
    public List<ChatMessage> getRecentContext(UUID sessionId, UUID userId, UUID tenantId, int limit) {
        List<ChatMessage> list = messageRepository.findTop10BySessionIdAndTenantIdAndUserIdOrderByCreatedAtDesc(sessionId, tenantId, userId);
        Collections.reverse(list); // restore chronological order
        return list;
    }
}
