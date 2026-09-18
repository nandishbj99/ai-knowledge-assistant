package com.knowledgeassistant.domain.repository;

import com.knowledgeassistant.domain.entity.ChatMessage;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ChatMessageRepository extends JpaRepository<ChatMessage, UUID> {
    List<ChatMessage> findAllBySessionIdAndTenantIdAndUserIdOrderByCreatedAtAsc(UUID sessionId, UUID tenantId, UUID userId);
    List<ChatMessage> findTop10BySessionIdAndTenantIdAndUserIdOrderByCreatedAtDesc(UUID sessionId, UUID tenantId, UUID userId);
    void deleteAllBySessionId(UUID sessionId);
}
