package org.example.chat.infrastructure.websocket;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.example.chat.infrastructure.security.ChatUserDetails;
import org.example.chat.infrastructure.security.JwtTokenProvider;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.http.server.ServletServerHttpRequest;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.simp.config.ChannelRegistration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.messaging.simp.stomp.StompCommand;
import org.springframework.messaging.simp.stomp.StompHeaderAccessor;
import org.springframework.messaging.support.ChannelInterceptor;
import org.springframework.messaging.support.MessageHeaderAccessor;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.util.StringUtils;
import org.springframework.web.socket.WebSocketHandler;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;
import org.springframework.web.socket.server.HandshakeInterceptor;

import java.util.Collections;
import java.util.List;
import java.util.Map;

@Slf4j
@Configuration
@EnableWebSocketMessageBroker
@RequiredArgsConstructor
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    private final JwtTokenProvider jwtTokenProvider;

    private HandshakeInterceptor createCookieHandshakeInterceptor() {
        return new HandshakeInterceptor() {
            @Override
            public boolean beforeHandshake(ServerHttpRequest request, ServerHttpResponse response,
                                          WebSocketHandler wsHandler, Map<String, Object> attributes) {
                if (request instanceof ServletServerHttpRequest servletRequest) {
                    HttpServletRequest httpRequest = servletRequest.getServletRequest();
                    if (httpRequest.getCookies() != null) {
                        for (Cookie cookie : httpRequest.getCookies()) {
                            if ("ACCESS_TOKEN".equals(cookie.getName()) && StringUtils.hasText(cookie.getValue())) {
                                attributes.put("ACCESS_TOKEN", cookie.getValue());
                                break;
                            }
                        }
                    }
                }
                return true;
            }

            @Override
            public void afterHandshake(ServerHttpRequest request, ServerHttpResponse response,
                                       WebSocketHandler wsHandler, Exception exception) {
            }
        };
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        HandshakeInterceptor cookieInterceptor = createCookieHandshakeInterceptor();
        registry.addEndpoint("/ws")
                .setAllowedOriginPatterns("*")
                .addInterceptors(cookieInterceptor)
                .withSockJS();
        registry.addEndpoint("/ws")
                .setAllowedOriginPatterns("*")
                .addInterceptors(cookieInterceptor);
    }

    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        registry.setApplicationDestinationPrefixes("/app");
        registry.enableSimpleBroker("/topic", "/user");
        registry.setUserDestinationPrefix("/user");
    }

    @Override
    public void configureClientInboundChannel(ChannelRegistration registration) {
        registration.interceptors(new ChannelInterceptor() {
            @Override
            public Message<?> preSend(Message<?> message, MessageChannel channel) {
                StompHeaderAccessor accessor =
                        MessageHeaderAccessor.getAccessor(message, StompHeaderAccessor.class);

                if (accessor != null && StompCommand.CONNECT.equals(accessor.getCommand())) {
                    String token = null;

                    // 1. Try Authorization header
                    List<String> authHeaders = accessor.getNativeHeader("Authorization");
                    if (authHeaders != null && !authHeaders.isEmpty()) {
                        String headerVal = authHeaders.get(0);
                        if (headerVal.startsWith("Bearer ")) {
                            token = headerVal.substring(7);
                        }
                    }

                    // 2. Try 'token' header
                    if (token == null) {
                        List<String> tokenHeaders = accessor.getNativeHeader("token");
                        if (tokenHeaders != null && !tokenHeaders.isEmpty()) {
                            token = tokenHeaders.get(0);
                        }
                    }

                    // 3. Try Cookie from WebSocket handshake session attributes
                    if (token == null && accessor.getSessionAttributes() != null) {
                        Object cookieVal = accessor.getSessionAttributes().get("ACCESS_TOKEN");
                        if (cookieVal instanceof String s && StringUtils.hasText(s)) {
                            token = s;
                        }
                    }

                    if (StringUtils.hasText(token) && jwtTokenProvider.validateToken(token)) {
                        String userId = jwtTokenProvider.getUserIdFromToken(token);
                        String email = jwtTokenProvider.getEmailFromToken(token);
                        ChatUserDetails userDetails = new ChatUserDetails(userId, email);
                        UsernamePasswordAuthenticationToken authentication =
                                new UsernamePasswordAuthenticationToken(userDetails, null, Collections.emptyList());

                        accessor.setUser(authentication);
                        SecurityContextHolder.getContext().setAuthentication(authentication);
                        log.info("[WebSocket] User connected: {} ({})", email, userId);
                    } else {
                        log.warn("[WebSocket] STOMP connect without valid JWT token");
                    }
                }
                return message;
            }
        });
    }
}
