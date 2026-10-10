FROM eclipse-temurin:21-jdk-jammy AS build
WORKDIR /workspace
COPY gradlew build.gradle settings.gradle gradle.properties ./
COPY gradle ./gradle
RUN --mount=type=cache,target=/root/.gradle \
    chmod +x gradlew && sed -i 's/networkTimeout=10000/networkTimeout=60000/; s/retries=0/retries=2/' gradle/wrapper/gradle-wrapper.properties \
    && ./gradlew --no-daemon --version
COPY src ./src
RUN --mount=type=cache,target=/root/.gradle ./gradlew --no-daemon bootJar -x test

FROM eclipse-temurin:21-jre-jammy
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 mathvision && useradd --uid 10001 --gid mathvision --no-create-home mathvision \
    && mkdir -p /app/uploads && chown mathvision:mathvision /app/uploads
WORKDIR /app
COPY --from=build /workspace/build/libs/business-api.jar ./business-api.jar
ENV SPRING_PROFILES_ACTIVE=prod PORT=8080 UPLOAD_ROOT=/app/uploads
USER mathvision
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/business-api.jar"]
