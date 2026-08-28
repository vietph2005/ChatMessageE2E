package org.example.chat.infrastructure.persistence.mongodb;

import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.config.EnableMongoAuditing;
import org.springframework.data.mongodb.repository.config.EnableMongoRepositories;

@Configuration
@EnableMongoAuditing
@EnableMongoRepositories(basePackages = "org.example.chat.infrastructure.persistence.mongodb.repository")
public class MongoConfig {
}
