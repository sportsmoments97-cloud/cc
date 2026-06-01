FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget gnupg2 unzip curl jq \
    fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libatspi2.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnspr4 libnss3 libwayland-client0 libxcomposite1 libxdamage1 \
    libxfixes3 libxkbcommon0 libxrandr2 libxshmfence1 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i /tmp/chrome.deb || apt-get install -f -y \
    && rm -f /tmp/chrome.deb

# Get matching chromedriver from Chrome for Testing
RUN CHROME_VERSION=$(google-chrome --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1) \
    && echo "Chrome version: ${CHROME_VERSION}" \
    && CFT_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json" \
       | jq -r --arg v "$CHROME_VERSION" '.versions[] | select(.version == $v) | .downloads.chromedriver[] | select(.platform == "linux64") | .url' | head -1) \
    && if [ -z "$CFT_URL" ]; then \
         echo "Exact match not found, trying last-versions endpoint" \
         && CFT_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json" \
            | jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform == "linux64") | .url'); \
       fi \
    && echo "Chromedriver URL: ${CFT_URL}" \
    && wget -q -O /tmp/chromedriver.zip "${CFT_URL}" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && find /tmp -name chromedriver -type f -exec mv {} /usr/local/bin/chromedriver \; \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver* \
    && echo "Chromedriver:" && chromedriver --version

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
