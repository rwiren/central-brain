FROM debian:bookworm-slim

# Install build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone and compile RTKLIB (demo5 branch)
WORKDIR /tmp
RUN git clone --branch demo5 --depth 1 https://github.com/rtklibexplorer/RTKLIB.git && \
    cd RTKLIB/app/consapp/str2str/gcc && \
    make && \
    mv str2str /usr/local/bin/ && \
    cd /tmp && rm -rf RTKLIB

# Copy the failover script
COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

# Run the Failover Script
CMD ["/usr/local/bin/start.sh"]
