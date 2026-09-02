package org.example.chat.infrastructure.rag;

public class RagApiException extends RuntimeException {
    public RagApiException(String message) {
        super(message);
    }

    public RagApiException(String message, Throwable cause) {
        super(message, cause);
    }
}
