from mitmproxy import http

# Variable to store the last captured headers as a string
last_headers_str = ""

def request(flow: http.HTTPFlow) -> None:
    global last_headers_str

    # Only capture Discord's API or asset requests
    if "discord.com" in flow.request.pretty_url:
        # Convert headers to string
        last_headers_str = str(flow.request.headers)

        # Print for debugging
        print("\n=== Discord Request Headers ===")
        print(last_headers_str)
        print("================================\n")

        # You can now use last_headers_str elsewhere
