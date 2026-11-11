package com.mathvisionkids.api;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
@org.springframework.scheduling.annotation.EnableScheduling
public class BusinessApiApplication {

	public static void main(String[] args) {
		// JDBC sends the JVM zone during connection startup. Use a portable IANA
		// zone instead of a Windows-derived legacy alias (for example Asia/Saigon).
		java.util.TimeZone.setDefault(java.util.TimeZone.getTimeZone("UTC"));
		SpringApplication.run(BusinessApiApplication.class, args);
	}

}
