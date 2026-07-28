package org.jejuro.miraero.mock_server.global.config;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.PropertySource;

@Configuration
@PropertySource("classpath:/application.properties")
@MapperScan("org.jejuro.miraero.mock_server.*.mapper")
public class MyBatisConfig {

}