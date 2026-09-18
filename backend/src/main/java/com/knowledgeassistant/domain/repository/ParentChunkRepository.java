package com.knowledgeassistant.domain.repository;

import com.knowledgeassistant.domain.entity.ParentChunk;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ParentChunkRepository extends JpaRepository<ParentChunk, UUID> {
    List<ParentChunk> findAllByDocumentId(UUID documentId);
    void deleteAllByDocumentId(UUID documentId);
}
