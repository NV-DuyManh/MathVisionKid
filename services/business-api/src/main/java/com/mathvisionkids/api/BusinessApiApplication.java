package com.mathvisionkids.api;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class BusinessApiApplication {

	public static void main(String[] args) {
		SpringApplication.run(BusinessApiApplication.class, args);
	}

}
