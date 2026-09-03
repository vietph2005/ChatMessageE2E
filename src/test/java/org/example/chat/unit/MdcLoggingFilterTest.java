package org.example.chat.unit;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import org.example.chat.infrastructure.logging.MdcLoggingFilter;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.slf4j.MDC;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

import java.io.IOException;

import static org.junit.jupiter.api.Assertions.*;

class MdcLoggingFilterTest {

    private final MdcLoggingFilter filter = new MdcLoggingFilter();

    @Test
    @DisplayName("Should use provided X-Trace-Id header and set response header")
    void shouldUseProvidedTraceId() throws ServletException, IOException {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("X-Trace-Id", "custom-trace-123");
        MockHttpServletResponse response = new MockHttpServletResponse();

        FilterChain filterChain = (req, res) -> {
            assertEquals("custom-trace-123", MDC.get("traceId"));
        };

        filter.doFilter(request, response, filterChain);

        assertEquals("custom-trace-123", response.getHeader("X-Trace-Id"));
        assertNull(MDC.get("traceId"), "MDC should be cleared after filter execution");
    }

    @Test
    @DisplayName("Should generate new traceId when X-Trace-Id header is absent")
    void shouldGenerateNewTraceIdWhenHeaderAbsent() throws ServletException, IOException {
        MockHttpServletRequest request = new MockHttpServletRequest();
        MockHttpServletResponse response = new MockHttpServletResponse();

        FilterChain filterChain = (req, res) -> {
            assertNotNull(MDC.get("traceId"));
            assertFalse(MDC.get("traceId").isBlank());
        };

        filter.doFilter(request, response, filterChain);

        String traceIdResponse = response.getHeader("X-Trace-Id");
        assertNotNull(traceIdResponse);
        assertFalse(traceIdResponse.isBlank());
        assertNull(MDC.get("traceId"), "MDC should be cleared after filter execution");
    }
}
