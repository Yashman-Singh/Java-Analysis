package com.example.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Bean;
import com.example.service.UserService;

@Configuration
public class AppConfig {
    @Bean
    public UserService userService() {
        return new UserService();
    }
} 