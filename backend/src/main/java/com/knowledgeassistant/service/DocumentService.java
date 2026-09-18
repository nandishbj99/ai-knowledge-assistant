package com.knowledgeassistant.service;

import com.knowledgeassistant.domain.entity.Document;
import com.knowledgeassistant.domain.repository.DocumentRepository;
import com.knowledgeassistant.domain.repository.ParentChunkRepository;
import com.knowledgeassistant.web.dto.DocumentResponse;
import com.knowledgeassistant.web.dto.DocumentStatusResponse;
import org.apache.tika.Tika;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.connection.stream.StreamRecords;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class DocumentService {

    private static final Logger log = LoggerFactory.getLogger(DocumentService.class);
    private static final Set<String> ALLOWED_MIME_TYPES = Set.of(
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
            "text/plain"
    );

    private final DocumentRepository documentRepository;
    private final ParentChunkRepository parentChunkRepository;
    private final StringRedisTemplate redisTemplate;
    private final Path storagePath;
    private final Tika tika;

    public DocumentService(
            DocumentRepository documentRepository,
            ParentChunkRepository parentChunkRepository,
            StringRedisTemplate redisTemplate,
            @Value("${app.storage.upload-dir:/shared/storage}") String uploadDir) {
        this.documentRepository = documentRepository;
        this.parentChunkRepository = parentChunkRepository;
        this.redisTemplate = redisTemplate;
        this.storagePath = Paths.get(uploadDir);
        this.tika = new Tika();

        try {
            Files.createDirectories(this.storagePath);
        } catch (IOException e) {
            log.warn("Could not create base upload directory: {}", uploadDir, e);
        }
    }

    @Transactional
    public DocumentResponse uploadDocument(UUID userId, UUID tenantId, MultipartFile file) throws IOException {
        if (file.isEmpty()) {
            throw new IllegalArgumentException("Cannot upload empty file");
        }

        String originalFilename = Objects.requireNonNullElse(file.getOriginalFilename(), "unnamed_document");

        // ADR-11: Validate MIME type via Apache Tika magic-byte inspection
        String detectedMime;
        try (InputStream is = new BufferedInputStream(file.getInputStream())) {
            detectedMime = tika.detect(is, originalFilename);
        }

        if (!ALLOWED_MIME_TYPES.contains(detectedMime)) {
            throw new IllegalArgumentException("Unsupported file type: " + detectedMime + ". Only PDF, DOCX, and TXT are permitted.");
        }

        // Prepare tenant-isolated storage path
        Path tenantDir = storagePath.resolve(tenantId.toString());
        Files.createDirectories(tenantDir);

        UUID docId = UUID.randomUUID();
        String fileExt = originalFilename.contains(".") ? originalFilename.substring(originalFilename.lastIndexOf(".")) : "";
        String targetFilename = docId + fileExt;
        Path destination = tenantDir.resolve(targetFilename);

        Files.copy(file.getInputStream(), destination, StandardCopyOption.REPLACE_EXISTING);

        // Create and persist Document entity
        Document document = new Document(userId, tenantId, originalFilename, destination.toAbsolutePath().toString(), file.getSize(), detectedMime);
        document.setId(docId);
        document.setStatus("PENDING");
        document = documentRepository.save(document);

        // ADR-01: Publish task to Redis Stream 'ingestion:tasks'
        Map<String, String> taskPayload = new HashMap<>();
        taskPayload.put("document_id", document.getId().toString());
        taskPayload.put("tenant_id", tenantId.toString());
        taskPayload.put("user_id", userId.toString());
        taskPayload.put("file_path", document.getFilePath());
        taskPayload.put("filename", document.getFilename());
        taskPayload.put("mime_type", document.getMimeType());

        MapRecord<String, String, String> record = StreamRecords.string(taskPayload).withStreamKey("ingestion:tasks");
        redisTemplate.opsForStream().add(record);
        log.info("Dispatched ingestion task for docId={} to stream ingestion:tasks", docId);

        return toResponse(document);
    }

    @Transactional(readOnly = true)
    public List<DocumentResponse> getDocuments(UUID userId, UUID tenantId) {
        return documentRepository.findAllByTenantIdAndUserIdOrderByCreatedAtDesc(tenantId, userId)
                .stream()
                .map(this::toResponse)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public DocumentResponse getDocument(UUID docId, UUID userId, UUID tenantId) {
        Document doc = documentRepository.findByIdAndTenantIdAndUserId(docId, tenantId, userId)
                .orElseThrow(() -> new NoSuchElementException("Document not found: " + docId));
        return toResponse(doc);
    }

    @Transactional(readOnly = true)
    public DocumentStatusResponse getDocumentStatus(UUID docId, UUID userId, UUID tenantId) {
        Document doc = documentRepository.findByIdAndTenantIdAndUserId(docId, tenantId, userId)
                .orElseThrow(() -> new NoSuchElementException("Document not found: " + docId));
        return new DocumentStatusResponse(doc.getId(), doc.getStatus(), doc.getTotalParentChunks(), doc.getTotalChildChunks(), doc.getErrorMessage());
    }

    @Transactional
    public void deleteDocument(UUID docId, UUID userId, UUID tenantId) {
        Document doc = documentRepository.findByIdAndTenantIdAndUserId(docId, tenantId, userId)
                .orElseThrow(() -> new NoSuchElementException("Document not found: " + docId));

        // Delete physical file
        try {
            Path filePath = Paths.get(doc.getFilePath());
            Files.deleteIfExists(filePath);
        } catch (Exception e) {
            log.warn("Failed to delete physical file for docId={}: {}", docId, e.getMessage());
        }

        // Delete parent chunks (cascades to document_chunks in DB)
        parentChunkRepository.deleteAllByDocumentId(docId);
        documentRepository.delete(doc);
        log.info("Successfully purged document and chunks: docId={}", docId);
    }

    private DocumentResponse toResponse(Document doc) {
        return new DocumentResponse(
                doc.getId(),
                doc.getFilename(),
                doc.getFileSize(),
                doc.getMimeType(),
                doc.getStatus(),
                doc.getTotalParentChunks(),
                doc.getTotalChildChunks(),
                doc.getErrorMessage(),
                doc.getCreatedAt()
        );
    }
}
