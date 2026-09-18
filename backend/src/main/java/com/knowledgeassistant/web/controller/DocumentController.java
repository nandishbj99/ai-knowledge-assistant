package com.knowledgeassistant.web.controller;

import com.knowledgeassistant.security.UserPrincipal;
import com.knowledgeassistant.service.DocumentService;
import com.knowledgeassistant.web.dto.DocumentResponse;
import com.knowledgeassistant.web.dto.DocumentStatusResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/documents")
public class DocumentController {

    private final DocumentService documentService;

    public DocumentController(DocumentService documentService) {
        this.documentService = documentService;
    }

    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<DocumentResponse> uploadDocument(
            @AuthenticationPrincipal UserPrincipal principal,
            @RequestParam("file") MultipartFile file) throws IOException {
        DocumentResponse response = documentService.uploadDocument(principal.getId(), principal.getTenantId(), file);
        return ResponseEntity.status(HttpStatus.ACCEPTED).body(response);
    }

    @GetMapping
    public ResponseEntity<List<DocumentResponse>> getDocuments(@AuthenticationPrincipal UserPrincipal principal) {
        List<DocumentResponse> list = documentService.getDocuments(principal.getId(), principal.getTenantId());
        return ResponseEntity.ok(list);
    }

    @GetMapping("/{id}")
    public ResponseEntity<DocumentResponse> getDocument(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID id) {
        DocumentResponse response = documentService.getDocument(id, principal.getId(), principal.getTenantId());
        return ResponseEntity.ok(response);
    }

    @GetMapping("/{id}/status")
    public ResponseEntity<DocumentStatusResponse> getDocumentStatus(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID id) {
        DocumentStatusResponse response = documentService.getDocumentStatus(id, principal.getId(), principal.getTenantId());
        return ResponseEntity.ok(response);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Map<String, String>> deleteDocument(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID id) {
        documentService.deleteDocument(id, principal.getId(), principal.getTenantId());
        return ResponseEntity.ok(Map.of("message", "Document deleted successfully"));
    }
}
