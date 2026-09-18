package com.knowledgeassistant.domain.repository;

import com.knowledgeassistant.domain.entity.Document;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface DocumentRepository extends JpaRepository<Document, UUID> {
    Optional<Document> findByIdAndTenantIdAndUserId(UUID id, UUID tenantId, UUID userId);
    List<Document> findAllByTenantIdAndUserIdOrderByCreatedAtDesc(UUID tenantId, UUID userId);
    void deleteByIdAndTenantIdAndUserId(UUID id, UUID tenantId, UUID userId);
}
