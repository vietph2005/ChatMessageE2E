package org.example.chat.presentation.exception;

import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.example.chat.domain.exception.DomainException;
import org.slf4j.MDC;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.Instant;
import java.util.UUID;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final String TRACE_ID_HEADER = "X-Trace-Id";
    private static final String MDC_TRACE_ID_KEY = "traceId";

    @ExceptionHandler(DomainException.class)
    public ResponseEntity<ApiError> handleDomainException(DomainException ex, HttpServletRequest request) {
        String traceId = resolveTraceId(request);
        log.warn("[DomainException] TraceId: {}, Code: {}, Message: {}", traceId, ex.getErrorCode(), ex.getMessage());

        ApiError error = ApiError.builder()
                .status(ex.getHttpStatus().value())
                .errorCode(ex.getErrorCode())
                .message(ex.getMessage())
                .traceId(traceId)
                .timestamp(Instant.now())
                .build();

        return ResponseEntity.status(ex.getHttpStatus()).body(error);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiError> handleValidationException(MethodArgumentNotValidException ex, HttpServletRequest request) {
        String traceId = resolveTraceId(request);
        String errorMessage = ex.getBindingResult().getFieldErrors().stream()
                .map(err -> err.getField() + ": " + err.getDefaultMessage())
                .reduce((a, b) -> a + ", " + b)
                .orElse("Validation failed");

        log.warn("[ValidationException] TraceId: {}, Errors: {}", traceId, errorMessage);

        ApiError error = ApiError.builder()
                .status(HttpStatus.BAD_REQUEST.value())
                .errorCode("VALIDATION_ERROR")
                .message(errorMessage)
                .traceId(traceId)
                .timestamp(Instant.now())
                .build();

        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }

    @ExceptionHandler(org.example.chat.infrastructure.rag.RagApiException.class)
    public ResponseEntity<ApiError> handleRagApiException(org.example.chat.infrastructure.rag.RagApiException ex, HttpServletRequest request) {
        String traceId = resolveTraceId(request);
        log.warn("[RagApiException] TraceId: {}, Message: {}", traceId, ex.getMessage());

        ApiError error = ApiError.builder()
                .status(HttpStatus.SERVICE_UNAVAILABLE.value())
                .errorCode("RAG_UNAVAILABLE")
                .message(ex.getMessage())
                .traceId(traceId)
                .timestamp(Instant.now())
                .build();

        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(error);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiError> handleGenericException(Exception ex, HttpServletRequest request) {
        String traceId = resolveTraceId(request);
        log.error("[UnhandledException] TraceId: {}, Error: {}", traceId, ex.getMessage(), ex);

        ApiError error = ApiError.builder()
                .status(HttpStatus.INTERNAL_SERVER_ERROR.value())
                .errorCode("INTERNAL_SERVER_ERROR")
                .message("An unexpected error occurred. Please contact support referencing trace ID: " + traceId)
                .traceId(traceId)
                .timestamp(Instant.now())
                .build();

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }

    private String resolveTraceId(HttpServletRequest request) {
        String traceId = request.getHeader(TRACE_ID_HEADER);
        if (traceId == null || traceId.isBlank()) {
            traceId = MDC.get(MDC_TRACE_ID_KEY);
        }
        if (traceId == null || traceId.isBlank()) {
            traceId = UUID.randomUUID().toString();
            MDC.put(MDC_TRACE_ID_KEY, traceId);
        }
        return traceId;
    }
}
