package com.knowledgeassistant.domain.repository;

import com.knowledgeassistant.domain.entity.ChatSession;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ChatSessionRepository extends JpaRepository<ChatSession, UUID> {
    Optional<ChatSession> findByIdAndTenantIdAndUserId(UUID id, UUID tenantId, UUID userId);
    List<ChatSession> findAllByTenantIdAndUserIdOrderByUpdatedAtDesc(UUID tenantId, UUID userId);
    void deleteByIdAndTenantIdAndUserId(UUID id, UUID tenantId, UUID userId);
}
