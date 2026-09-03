package org.example.chat.infrastructure.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

@Configuration
public class ChatbotConfig {

    @Value("${rag.service.connect-timeout-seconds:10}")
    private int connectTimeoutSeconds;

    @Value("${rag.service.read-timeout-seconds:60}")
    private int readTimeoutSeconds;

    @Bean(name = "ragRestTemplate")
    public RestTemplate ragRestTemplate(RestTemplateBuilder builder) {
        return builder
                .setConnectTimeout(Duration.ofSeconds(connectTimeoutSeconds))
                .setReadTimeout(Duration.ofSeconds(readTimeoutSeconds))
                .build();
    }
}
