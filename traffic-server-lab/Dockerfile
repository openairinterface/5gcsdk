# Build traffic-server
FROM ubuntu:20.04 AS traffic-server-build
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Paris

# Set the working directory to /traffic-server
WORKDIR /traffic-server

# Copy the trafficserver.py and lib file into the container
COPY libtraffic/ /traffic-server/libtraffic/
COPY trafficserver.py . /traffic-server/

# Expose port 5000 for traffic-server
EXPOSE 5000

# Stage 2: Build ue-identity-server
FROM ubuntu:20.04 AS ue-identity-server-build
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Paris

# Set the working directory to /app/ue-identity-server
WORKDIR /ue-identity-server

# Copy the application files into the container
COPY libtraffic/ /ue-identity-server/libtraffic/
COPY ueidentityserver.py . /ue-identity-server/

# Expose ports 38412 and 80 for ue-identity-server
EXPOSE 38412/sctp
EXPOSE 80/tcp

# Final stage: Create production images
FROM ubuntu:20.04 AS traffic-enabler
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Paris

# Install dependencies and debug tools for traffic-server
RUN apt-get update && \
    apt-get install -y \
      psmisc \
      net-tools \
      tshark \
      tzdata \
      iperf3 \
      iproute2 \
      iputils-ping \
      iptables \
      traceroute \
      tcpdump \
      iperf3 \
      python3 \
      python3-pip \
      software-properties-common \
      curl \
      iperf3 \
      dnsutils \
    && pip3 install Flask numpy kubernetes \
    && add-apt-repository -y ppa:deadsnakes/ppa

RUN apt update && \
      apt install -y curl && \
      curl -LO https://storage.googleapis.com/kubernetes-release/release/`curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt`/bin/linux/amd64/kubectl && \
      chmod +x ./kubectl && \
      mv ./kubectl /usr/local/bin/kubectl

# Copy built artifacts from traffic-server-build stage
COPY --from=traffic-server-build /traffic-server /traffic-server

# Copy built artifacts from ue-identity-server-build stage
COPY --from=ue-identity-server-build /ue-identity-server /ue-identity-server

# Install Python dependencies for ue-identity-server
RUN pip3 install -r /ue-identity-server/libtraffic/requirements.txt
