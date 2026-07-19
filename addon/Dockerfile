ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install required packages
RUN apk add --no-cache \
    rtl_433 \
    python3 \
    py3-pip \
    bash

# Set working directory
WORKDIR /app

# Copy bridge application
COPY bridge/ /app/

# Install Python dependencies (to be added later)
RUN if [ -f requirements.txt ]; then \
        pip3 install --no-cache-dir -r requirements.txt; \
    fi

# Copy startup script
COPY addon/run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
