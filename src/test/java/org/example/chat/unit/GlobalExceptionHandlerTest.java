package org.example.chat.unit;

import jakarta.servlet.http.HttpServletRequest;
import org.example.chat.domain.exception.DomainException;
import org.example.chat.infrastructure.rag.RagApiException;
import org.example.chat.presentation.exception.ApiError;
import org.example.chat.presentation.exception.GlobalExceptionHandler;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.core.MethodParameter;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindingResult;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class GlobalExceptionHandlerTest {

    private GlobalExceptionHandler exceptionHandler;

    @Mock
    private HttpServletRequest request;

    @Mock
    private BindingResult bindingResult;

    @BeforeEach
    void setUp() {
        exceptionHandler = new GlobalExceptionHandler();
    }

    @Test
    @DisplayName("Should handle DomainException and return corresponding HTTP status and ApiError")
    void shouldHandleDomainException() {
        when(request.getHeader("X-Trace-Id")).thenReturn("trace-12345");

        DomainException domainException = new DomainException("USER_NOT_FOUND", "User not found with given email", HttpStatus.NOT_FOUND);

        ResponseEntity<ApiError> response = exceptionHandler.handleDomainException(domainException, request);

        assertNotNull(response);
        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(404, response.getBody().getStatus());
        assertEquals("USER_NOT_FOUND", response.getBody().getErrorCode());
        assertEquals("User not found with given email", response.getBody().getMessage());
        assertEquals("trace-12345", response.getBody().getTraceId());
        assertNotNull(response.getBody().getTimestamp());
    }

    @Test
    @DisplayName("Should handle MethodArgumentNotValidException and return 400 Bad Request with field errors")
    void shouldHandleValidationException() {
        when(request.getHeader("X-Trace-Id")).thenReturn(null);

        FieldError fieldError = new FieldError("object", "email", "must not be blank");
        when(bindingResult.getFieldErrors()).thenReturn(List.of(fieldError));

        MethodArgumentNotValidException validationException = new MethodArgumentNotValidException(
                (MethodParameter) null, bindingResult
        );

        ResponseEntity<ApiError> response = exceptionHandler.handleValidationException(validationException, request);

        assertNotNull(response);
        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(400, response.getBody().getStatus());
        assertEquals("VALIDATION_ERROR", response.getBody().getErrorCode());
        assertTrue(response.getBody().getMessage().contains("email: must not be blank"));
        assertNotNull(response.getBody().getTraceId());
    }

    @Test
    @DisplayName("Should handle RagApiException and return 503 Service Unavailable")
    void shouldHandleRagApiException() {
        when(request.getHeader("X-Trace-Id")).thenReturn("trace-rag-99");

        RagApiException ragException = new RagApiException("RAG microservice is offline");

        ResponseEntity<ApiError> response = exceptionHandler.handleRagApiException(ragException, request);

        assertNotNull(response);
        assertEquals(HttpStatus.SERVICE_UNAVAILABLE, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(503, response.getBody().getStatus());
        assertEquals("RAG_UNAVAILABLE", response.getBody().getErrorCode());
        assertEquals("RAG microservice is offline", response.getBody().getMessage());
        assertEquals("trace-rag-99", response.getBody().getTraceId());
    }

    @Test
    @DisplayName("Should handle generic unhandled Exception and return 500 Internal Server Error")
    void shouldHandleGenericException() {
        when(request.getHeader("X-Trace-Id")).thenReturn("trace-unhandled");

        RuntimeException genericException = new RuntimeException("Unexpected null pointer");

        ResponseEntity<ApiError> response = exceptionHandler.handleGenericException(genericException, request);

        assertNotNull(response);
        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(500, response.getBody().getStatus());
        assertEquals("INTERNAL_SERVER_ERROR", response.getBody().getErrorCode());
        assertTrue(response.getBody().getMessage().contains("trace-unhandled"));
    }
}
