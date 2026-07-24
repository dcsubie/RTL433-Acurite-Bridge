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

# Copy Python application
COPY bridge/ /app/bridge/

# Copy Python requirements
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Copy startup script
COPY run.sh /run.sh
RUN chmod +x /run.sh

ENTRYPOINT ["/run.sh"]
