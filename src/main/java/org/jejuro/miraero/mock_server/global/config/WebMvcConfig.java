package org.jejuro.miraero.mock_server.global.config;

import lombok.RequiredArgsConstructor;
import org.jejuro.miraero.mock_server.global.interceptor.ClientSecretInterceptor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
@RequiredArgsConstructor
public class WebMvcConfig implements WebMvcConfigurer {

    private final ClientSecretInterceptor clientSecretInterceptor;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(clientSecretInterceptor)
                .addPathPatterns("/mock/oauth/**");
    }
}
