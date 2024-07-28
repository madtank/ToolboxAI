# Use Amazon Linux 2023 as the base image
FROM amazonlinux:2023

# Set the working directory in the container
WORKDIR /app

# Install system dependencies and Python
RUN dnf update -y && \
    dnf install -y --allowerasing \
    python3 \
    python3-pip \
    python3-devel \
    gcc \
    curl \
    wget \
    git \
    vim-minimal \
    nano \
    tmux \
    jq \
    nodejs \
    npm \
    unzip \
    net-tools \
    iputils \
    bind-utils \
    && dnf clean all

# Create and activate virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python packages
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Install additional useful Python packages
RUN pip3 install --no-cache-dir \
    requests \
    beautifulsoup4 \
    praw \
    tweepy \
    psutil \
    python-dotenv \
    pyyaml \
    schedule \
    colorama \
    tqdm \
    pytz \
    faker \
    python-dateutil \
    pymongo \
    redis \
    asyncio \
    aiohttp

# Copy the main application file
COPY main.py .

# Copy the src directory
COPY src/ ./src/

# Copy other necessary files (adjust as needed)
COPY assets/ ./assets/

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true

# Run streamlit when the container launches
CMD ["streamlit", "run", "main.py"]