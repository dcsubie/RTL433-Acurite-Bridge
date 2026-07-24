ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install required packages
RUN apk add --no-cache \
    rtl_433 \
    python3 \
    py3-paho-mqtt \
    bash

# Set working directory
WORKDIR /app

# Copy Python application
COPY bridge/ /app/bridge/


# Copy startup script
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
