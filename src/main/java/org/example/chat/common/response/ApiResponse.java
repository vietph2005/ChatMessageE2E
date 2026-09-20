package org.example.chat.common.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.Instant;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ApiResponse<T> {

    private boolean success;
    private String code;           // Ví dụ: "SUCCESS", "USER_NOT_FOUND", "VALIDATION_ERROR"
    private String message;
    private T data;
    private Object errors;         // Chứa mảng/object chi tiết lỗi validation (nếu có)

    @Builder.Default
    private Instant timestamp = Instant.now();

    // 1. Success có data
    public static <T> ApiResponse<T> success(T data) {
        return ApiResponse.<T>builder()
                .success(true)
                .code("SUCCESS")
                .message("Request processed successfully")
                .data(data)
                .build();
    }

    // 2. Success có message tùy chỉnh + data
    public static <T> ApiResponse<T> success(String message, T data) {
        return ApiResponse.<T>builder()
                .success(true)
                .code("SUCCESS")
                .message(message)
                .data(data)
                .build();
    }

    // 3. Error đơn giản (có mã code lỗi định danh)
    public static <T> ApiResponse<T> error(String code, String errorMessage) {
        return ApiResponse.<T>builder()
                .success(false)
                .code(code)
                .message(errorMessage)
                .build();
    }

    // 4. Error kèm chi tiết validation form
    public static <T> ApiResponse<T> error(String code, String errorMessage, Object errors) {
        return ApiResponse.<T>builder()
                .success(false)
                .code(code)
                .message(errorMessage)
                .errors(errors)
                .build();
    }
}